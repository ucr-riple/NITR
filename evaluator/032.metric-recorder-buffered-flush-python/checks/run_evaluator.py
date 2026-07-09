#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
from pathlib import Path

CONCRETE_RECORDER_NAMES = {"ConsoleMetricRecorder", "BufferedMetricRecorder"}
CAPABILITY_METHOD_NAMES = {
    "is_buffered",
    "supports_flush",
    "can_flush",
    "has_buffer",
    "needs_flush",
    "requires_flush",
}


@dataclass
class FunctionInfo:
    function_id: str
    name: str
    qualname: str
    path: Path
    calls: set[str] = field(default_factory=set)
    concrete_refs: set[str] = field(default_factory=set)
    capability_branching: bool = False


class ClassAttributeScanner(ast.NodeVisitor):
    def __init__(self) -> None:
        self.attrs: set[str] = set()

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            attr_name = self._self_attr_name(target)
            if attr_name is not None:
                self.attrs.add(attr_name)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        attr_name = self._self_attr_name(node.target)
        if attr_name is not None:
            self.attrs.add(attr_name)
        self.generic_visit(node)

    def _self_attr_name(self, node: ast.AST) -> str | None:
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
        ):
            return node.attr
        return None


class FunctionScanner(ast.NodeVisitor):
    def __init__(self, info: FunctionInfo) -> None:
        self.info = info

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in CONCRETE_RECORDER_NAMES:
            self.info.concrete_refs.add(node.id)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        called_name = self._called_name(node.func)
        if called_name is not None:
            self.info.calls.add(called_name)

        if isinstance(node.func, ast.Name) and node.func.id == "isinstance":
            if any(self._references_recorder(arg) for arg in node.args):
                self.info.capability_branching = True
        if isinstance(node.func, ast.Name) and node.func.id == "hasattr":
            if node.args and self._references_recorder(node.args[0]):
                self.info.capability_branching = True
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in CAPABILITY_METHOD_NAMES
        ):
            if self._references_recorder(node.func.value):
                self.info.capability_branching = True

        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        if self._has_recorder_capability_check(node.test):
            self.info.capability_branching = True
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        if self._has_recorder_capability_check(node.test):
            self.info.capability_branching = True
        self.generic_visit(node)

    def _called_name(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _has_recorder_capability_check(self, node: ast.AST) -> bool:
        for test_node in ast.walk(node):
            if isinstance(test_node, ast.Call):
                if isinstance(test_node.func, ast.Name) and test_node.func.id in {
                    "isinstance",
                    "hasattr",
                }:
                    if any(self._references_recorder(arg) for arg in test_node.args):
                        return True
                if (
                    isinstance(test_node.func, ast.Attribute)
                    and test_node.func.attr in CAPABILITY_METHOD_NAMES
                    and self._references_recorder(test_node.func.value)
                ):
                    return True
        return False

    def _references_recorder(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id == "recorder"
        if isinstance(node, ast.Attribute):
            return (
                isinstance(node.value, ast.Name)
                and node.value.id == "self"
                and node.attr == "_recorder"
            )
        return False


class ModuleInfo(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.class_bases: dict[str, list[str]] = {}
        self.class_methods: dict[str, set[str]] = {}
        self.class_attrs: dict[str, set[str]] = {}
        self.functions: list[FunctionInfo] = []
        self.class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases: list[str] = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)
        self.class_bases[node.name] = bases

        methods = {
            child.name
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.class_methods[node.name] = methods

        attr_scanner = ClassAttributeScanner()
        for child in node.body:
            attr_scanner.visit(child)
        self.class_attrs[node.name] = attr_scanner.attrs

        self.class_stack.append(node.name)
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.visit(child)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        qualname = (
            ".".join([*self.class_stack, node.name]) if self.class_stack else node.name
        )
        info = FunctionInfo(
            function_id=qualname,
            name=node.name,
            qualname=qualname,
            path=self.path,
        )
        scanner = FunctionScanner(info)
        for statement in node.body:
            scanner.visit(statement)
        self.functions.append(info)
        if not self.class_stack:
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.visit(child)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)


def parse_module(path: Path) -> ModuleInfo:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    info = ModuleInfo(path)
    info.visit(tree)
    return info


def parse_src_modules(
    src_dir: Path,
) -> tuple[dict[Path, ModuleInfo], list[FunctionInfo]]:
    modules: dict[Path, ModuleInfo] = {}
    functions: list[FunctionInfo] = []
    for path in sorted(src_dir.rglob("*.py")):
        info = parse_module(path)
        modules[path] = info
        functions.extend(info.functions)
    return modules, functions


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

    return {
        function.function_id: {
            unique_name_to_id[callee]
            for callee in function.calls
            if callee in unique_name_to_id
        }
        for function in functions
    }


def reachable_from(entries: set[str], call_map: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    stack = list(entries)
    while stack:
        function_id = stack.pop()
        if function_id in seen:
            continue
        seen.add(function_id)
        for callee_id in call_map.get(function_id, set()):
            if callee_id not in seen:
                stack.append(callee_id)
    return seen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    src_dir = case_root / "src"

    metric_recorder_path = src_dir / "metric_recorder.py"
    console_path = src_dir / "console_metric_recorder.py"
    collector_path = src_dir / "metric_collector.py"
    buffered_path = src_dir / "buffered_metric_recorder.py"

    required_paths = [metric_recorder_path, console_path, collector_path]
    findings: list[str] = []
    for path in required_paths:
        if not path.is_file():
            findings.append(f"missing required path: {path.relative_to(case_root)}")

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    module_infos, all_functions = parse_src_modules(src_dir)
    metric_info = module_infos[metric_recorder_path]
    console_info = module_infos[console_path]
    collector_info = module_infos[collector_path]
    buffered_info = module_infos.get(buffered_path) if buffered_path.is_file() else None

    metric_methods = metric_info.class_methods.get("MetricRecorder", set())
    if "record" not in metric_methods:
        findings.append(
            "metric_recorder.py: MetricRecorder must declare record() on the abstract base."
        )
    if "flush" not in metric_methods:
        findings.append(
            "metric_recorder.py: MetricRecorder must admit a polymorphic visibility-trigger such as flush() alongside record()."
        )

    console_methods = console_info.class_methods.get("ConsoleMetricRecorder", set())
    if "record" not in console_methods:
        findings.append(
            "console_metric_recorder.py: ConsoleMetricRecorder must override record()."
        )

    if not buffered_path.is_file():
        findings.append(
            "src/buffered_metric_recorder.py is missing. The new buffered implementation must derive from MetricRecorder."
        )
    else:
        buffered_bases = buffered_info.class_bases.get("BufferedMetricRecorder", [])
        if "MetricRecorder" not in buffered_bases:
            findings.append(
                "buffered_metric_recorder.py: BufferedMetricRecorder must derive from MetricRecorder."
            )
        buffered_methods = buffered_info.class_methods.get(
            "BufferedMetricRecorder", set()
        )
        if "record" not in buffered_methods:
            findings.append(
                "buffered_metric_recorder.py: BufferedMetricRecorder must override record()."
            )
        if "flush" not in buffered_methods:
            findings.append(
                "buffered_metric_recorder.py: BufferedMetricRecorder must implement the visibility-trigger override."
            )
        buffered_attrs = buffered_info.class_attrs.get("BufferedMetricRecorder", set())
        if not any("buffer" in attr.lower() for attr in buffered_attrs):
            findings.append(
                "buffered_metric_recorder.py: BufferedMetricRecorder should own explicit buffer state on the implementation itself."
            )
        if not any("capacity" in attr.lower() for attr in buffered_attrs):
            findings.append(
                "buffered_metric_recorder.py: BufferedMetricRecorder should own explicit capacity state on the implementation itself."
            )

    collector_methods = collector_info.class_methods.get("MetricCollector", set())
    if "checkpoint" not in collector_methods:
        findings.append(
            "metric_collector.py: MetricCollector must define checkpoint() so callers can trigger metric visibility at the checkpoint boundary."
        )

    collector_entries = {
        function.function_id
        for function in all_functions
        if function.path == collector_path
        and function.qualname.startswith("MetricCollector.")
    }
    collector_functions_by_id = {
        function.function_id: function for function in all_functions
    }
    collector_reachable = reachable_from(
        collector_entries,
        build_call_map(all_functions),
    )

    concrete_refs = set()
    capability_branching = False
    for function_id in collector_reachable:
        function = collector_functions_by_id[function_id]
        concrete_refs |= function.concrete_refs
        capability_branching = capability_branching or function.capability_branching

    if concrete_refs:
        findings.append(
            "metric_collector.py: reachable collector behavior references concrete recorder types "
            f"({', '.join(sorted(concrete_refs))}) instead of operating through MetricRecorder."
        )
    if capability_branching:
        findings.append(
            "metric_collector.py: reachable collector behavior contains capability branching (for example isinstance/hasattr or flush-capability predicates). The checkpoint operation must call the polymorphic visibility-trigger through the abstract recorder reference without branching on implementation details."
        )

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: structural checks succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
