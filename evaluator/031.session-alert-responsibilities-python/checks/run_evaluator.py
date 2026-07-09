#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
from pathlib import Path

FAMILIES = ("range", "drift", "leak")
ALERT_TYPE_TO_FAMILY = {
    "RangeAlert": "range",
    "DriftAlert": "drift",
    "LeakAlert": "leak",
}
ALERT_LIST_ATTRS = {f"{family}_alerts": family for family in FAMILIES}


@dataclass
class FunctionInfo:
    function_id: str
    name: str
    qualname: str
    path: Path
    produced_families: set[str] = field(default_factory=set)
    signaled_families: set[str] = field(default_factory=set)
    calls: set[str] = field(default_factory=set)
    scans_events: bool = False


def attr_chain(node: ast.AST) -> list[str] | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return list(reversed(parts))
    return None


def family_from_alert_expr(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return ALERT_TYPE_TO_FAMILY.get(node.id)
    if isinstance(node, ast.Attribute):
        return ALERT_TYPE_TO_FAMILY.get(node.attr)
    return None


class FunctionAnalyzer(ast.NodeVisitor):
    def __init__(self, info: FunctionInfo) -> None:
        self.info = info
        self.aliases: dict[str, str] = {}

    def visit_Assign(self, node: ast.Assign) -> None:
        family = self._family_for_expr(node.value)
        if family is not None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.aliases[target.id] = family
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        family = self._family_for_expr(node.value) if node.value is not None else None
        if family is not None and isinstance(node.target, ast.Name):
            self.aliases[node.target.id] = family
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        family = family_from_alert_expr(node.func)
        if family is not None:
            self.info.produced_families.add(family)

        called_name = self._called_name(node.func)
        if called_name is not None:
            self.info.calls.add(called_name)

        if isinstance(node.func, ast.Attribute) and node.func.attr == "append":
            family = self._family_for_expr(node.func.value)
            if family is not None:
                self.info.produced_families.add(family)

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in {"low_bound", "high_bound"}:
            self.info.signaled_families.add("range")
        elif node.attr == "drift_tolerance":
            self.info.signaled_families.add("drift")
        elif node.attr in {"ACQUIRE", "RELEASE"}:
            self.info.signaled_families.add("leak")
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        if self._iterates_over_events(node.iter):
            self.info.scans_events = True
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        if self._iterates_over_events(node.iter):
            self.info.scans_events = True
        self.generic_visit(node)

    def _family_for_expr(self, node: ast.AST | None) -> str | None:
        if node is None:
            return None
        if isinstance(node, ast.Name):
            return self.aliases.get(node.id)
        if isinstance(node, ast.Attribute):
            chain = attr_chain(node)
            if chain is None:
                return None
            if chain[-1] in ALERT_LIST_ATTRS:
                return ALERT_LIST_ATTRS[chain[-1]]
        return None

    def _called_name(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _iterates_over_events(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id == "events"
        if isinstance(node, ast.Call):
            return any(self._iterates_over_events(arg) for arg in node.args)
        return False


class ModuleScanner(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.class_stack: list[str] = []
        self.functions: list[FunctionInfo] = []
        self.local_name_to_id: dict[str, str] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        qualname = (
            ".".join([*self.class_stack, node.name]) if self.class_stack else node.name
        )
        function_id = f"{self.path}:{qualname}"
        info = FunctionInfo(
            function_id=function_id,
            name=node.name,
            qualname=qualname,
            path=self.path,
        )
        self.local_name_to_id[node.name] = function_id
        analyzer = FunctionAnalyzer(info)
        for statement in node.body:
            analyzer.visit(statement)
        self.functions.append(info)
        # Do not descend here again; statements already analyzed.

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)


def scan_case_functions(case_root: Path) -> list[FunctionInfo]:
    functions: list[FunctionInfo] = []
    for path in sorted((case_root / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        scanner = ModuleScanner(path.relative_to(case_root))
        scanner.visit(tree)
        functions.extend(scanner.functions)
    return functions


def build_call_map(functions: list[FunctionInfo]) -> dict[str, set[str]]:
    unique_name_to_id: dict[str, str] = {}
    ambiguous_names: set[str] = set()

    for function in functions:
        if function.name in ambiguous_names:
            continue
        existing = unique_name_to_id.get(function.name)
        if existing is None:
            unique_name_to_id[function.name] = function.function_id
        else:
            ambiguous_names.add(function.name)
            unique_name_to_id.pop(function.name, None)

    call_map: dict[str, set[str]] = {}
    for function in functions:
        resolved_callees = {
            unique_name_to_id[callee]
            for callee in function.calls
            if callee in unique_name_to_id
        }
        call_map[function.function_id] = resolved_callees

    return call_map


def reachable_from(entry: str, call_map: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    stack = [entry]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        for callee in call_map.get(name, set()):
            if callee not in seen:
                stack.append(callee)
    return seen


def reverse_call_map(call_map: dict[str, set[str]]) -> dict[str, set[str]]:
    reverse: dict[str, set[str]] = {function_id: set() for function_id in call_map}
    for caller_id, callees in call_map.items():
        for callee_id in callees:
            reverse.setdefault(callee_id, set()).add(caller_id)
    return reverse


def caller_reachable_from(entry: str, reverse_map: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    stack = [entry]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        for caller in reverse_map.get(name, set()):
            if caller not in seen:
                stack.append(caller)
    return seen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    monitor_path = case_root / "src" / "monitor.py"
    findings: list[str] = []

    if not monitor_path.is_file():
        findings.append("missing required path: src/monitor.py")
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    try:
        functions = scan_case_functions(case_root)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: could not analyze source files: {exc}")
        return 1

    if not functions:
        print("FAIL: no Python functions found under src/")
        return 1

    functions_by_id = {function.function_id: function for function in functions}
    call_map = build_call_map(functions)
    reverse_map = reverse_call_map(call_map)

    for function in functions:
        observed_families = function.produced_families | function.signaled_families
        if len(observed_families) >= 2:
            family_list = ", ".join(sorted(observed_families))
            findings.append(
                f"{function.path}: function '{function.qualname}' mixes multiple alert families ({family_list}). "
                "Each anomaly family should be owned by its own unit."
            )

    analyze_functions = [
        function for function in functions if function.name == "analyze"
    ]
    if len(analyze_functions) != 1:
        findings.append(
            "Public entry analyze() is missing. It must remain defined and callable by the functional tests."
        )
        reachable = set()
    else:
        reachable = reachable_from(analyze_functions[0].function_id, call_map)

    produced_reachable: set[str] = set()
    for function_id in reachable:
        function = functions_by_id[function_id]
        produced_reachable |= function.produced_families | function.signaled_families

    single_family_producers = {
        function_id
        for function_id in reachable
        if len(
            functions_by_id[function_id].produced_families
            | functions_by_id[function_id].signaled_families
        )
        == 1
    }

    for function_id in reachable:
        function = functions_by_id[function_id]
        if function.name == "analyze" or not function.scans_events:
            continue
        caller_families: set[str] = set()
        for caller_id in caller_reachable_from(function_id, reverse_map):
            if caller_id in single_family_producers:
                caller = functions_by_id[caller_id]
                caller_families |= caller.produced_families | caller.signaled_families
        if len(caller_families) >= 2:
            findings.append(
                f"{function.path}: function '{function.qualname}' scans the event stream but is shared by multiple alert families "
                f"({', '.join(sorted(caller_families))}). Event-stream analysis should remain family-owned rather than funneled through a shared helper."
            )

    missing_families = set(FAMILIES) - produced_reachable
    if missing_families:
        findings.append(
            "No reachable producer found for alert families: "
            f"{', '.join(sorted(missing_families))}. Each family must be produced by code that analyze() invokes."
        )

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: structural checks succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
