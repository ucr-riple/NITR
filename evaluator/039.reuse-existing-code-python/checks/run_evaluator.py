#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
from pathlib import Path

CANONICAL_HELPERS = {"dot_product", "l2_norm"}


@dataclass
class FunctionInfo:
    name: str
    calls: set[str] = field(default_factory=set)
    helper_calls: set[str] = field(default_factory=set)
    has_manual_loop: bool = False
    has_manual_comprehension: bool = False
    has_norm_primitive: bool = False


def dotted_name(node: ast.AST) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def multiplication_inside(node: ast.AST) -> bool:
    return any(
        isinstance(child, ast.BinOp) and isinstance(child.op, ast.Mult)
        for child in ast.walk(node)
    )


def resolve_module_call(called: str, module_aliases: dict[str, str]) -> str | None:
    matching_prefixes = [
        prefix
        for prefix in module_aliases
        if called == prefix or called.startswith(f"{prefix}.")
    ]
    if not matching_prefixes:
        return None

    visible_prefix = max(matching_prefixes, key=len)
    canonical_module = module_aliases[visible_prefix]
    return canonical_module + called[len(visible_prefix) :]


class FunctionAnalyzer(ast.NodeVisitor):
    def __init__(
        self,
        info: FunctionInfo,
        direct_aliases: dict[str, str],
        module_aliases: dict[str, str],
    ) -> None:
        self.info = info
        self.direct_aliases = direct_aliases
        self.module_aliases = module_aliases

    def visit_Call(self, node: ast.Call) -> None:
        called = dotted_name(node.func)
        if called is not None:
            self.info.calls.add(called.split(".")[-1])
            if called in self.direct_aliases:
                self.info.helper_calls.add(self.direct_aliases[called])
            else:
                canonical_call = resolve_module_call(called, self.module_aliases)
                if canonical_call is not None:
                    parts = canonical_call.split(".")
                    if parts[-2:] == ["dot_product", "dot_product"]:
                        self.info.helper_calls.add("dot_product")
                    if parts[-2:] == ["l2_norm", "l2_norm"]:
                        self.info.helper_calls.add("l2_norm")
            if called in {"sqrt", "math.sqrt", "hypot", "math.hypot"}:
                self.info.has_norm_primitive = True
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.info.has_manual_loop = True
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.info.has_manual_loop = True
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        if multiplication_inside(node):
            self.info.has_manual_comprehension = True
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        if multiplication_inside(node):
            self.info.has_manual_comprehension = True
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        if multiplication_inside(node):
            self.info.has_manual_comprehension = True
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        if multiplication_inside(node):
            self.info.has_manual_comprehension = True
        self.generic_visit(node)


def import_aliases(tree: ast.Module) -> tuple[dict[str, str], dict[str, str]]:
    direct_aliases: dict[str, str] = {}
    module_aliases: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if (
                    node.module
                    and alias.name in CANONICAL_HELPERS
                    and node.module.endswith(alias.name)
                ):
                    direct_aliases[alias.asname or alias.name] = alias.name
                elif alias.name in CANONICAL_HELPERS and (node.module in {None, "src"}):
                    visible_name = alias.asname or alias.name
                    canonical_module = (
                        alias.name
                        if node.module is None
                        else f"{node.module}.{alias.name}"
                    )
                    module_aliases[visible_name] = canonical_module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                visible_prefix = alias.asname or alias.name
                module_aliases[visible_prefix] = alias.name
    return direct_aliases, module_aliases


def reachable_functions(entry: str, functions: dict[str, FunctionInfo]) -> set[str]:
    reachable: set[str] = set()
    stack = [entry]
    while stack:
        name = stack.pop()
        if name in reachable or name not in functions:
            continue
        reachable.add(name)
        stack.extend(functions[name].calls)
    return reachable


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    cosine_path = case_root / "src" / "cosine_similarity.py"
    if not cosine_path.is_file():
        print("FAIL: missing required path: src/cosine_similarity.py")
        return 1

    try:
        tree = ast.parse(
            cosine_path.read_text(encoding="utf-8"), filename=str(cosine_path)
        )
    except (OSError, SyntaxError) as exc:
        print(f"FAIL: could not analyze src/cosine_similarity.py: {exc}")
        return 1

    direct_aliases, module_aliases = import_aliases(tree)
    functions: dict[str, FunctionInfo] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        info = FunctionInfo(node.name)
        analyzer = FunctionAnalyzer(info, direct_aliases, module_aliases)
        for statement in node.body:
            analyzer.visit(statement)
        functions[node.name] = info

    findings: list[str] = []
    if "cosine_similarity" not in functions:
        findings.append("src/cosine_similarity.py must define cosine_similarity()")
        reachable: set[str] = set()
    else:
        reachable = reachable_functions("cosine_similarity", functions)

    helper_calls: set[str] = set()
    for name in reachable:
        info = functions[name]
        helper_calls.update(info.helper_calls)
        if info.has_manual_loop:
            findings.append(
                f"reachable function '{name}' contains a manual loop instead of "
                "reusing vector math helpers"
            )
        if info.has_manual_comprehension:
            findings.append(
                f"reachable function '{name}' contains multiplication inside a "
                "comprehension instead of reusing vector math helpers"
            )
        if info.has_norm_primitive:
            findings.append(
                f"reachable function '{name}' calls a norm primitive instead of "
                "reusing l2_norm()"
            )

    missing_helpers = CANONICAL_HELPERS - helper_calls
    if missing_helpers:
        findings.append(
            "cosine_similarity() must reach calls to existing helpers: "
            + ", ".join(sorted(missing_helpers))
        )

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: cosine_similarity reuses existing vector math helpers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
