#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from pathlib import Path

CACHE_CONTROL_PARAMETERS = {
    "use_cache",
    "force_refresh",
    "cache_key",
    "bypass_cache",
}
CACHE_STATE_TOKENS = ("cache", "cached", "last_summary", "last_products")


def assigned_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        return [name for element in node.elts for name in assigned_names(element)]
    return []


def statement_targets(node: ast.stmt) -> list[str]:
    if isinstance(node, ast.Assign):
        return [name for target in node.targets for name in assigned_names(target)]
    if isinstance(node, ast.AnnAssign):
        return assigned_names(node.target)
    return []


def function_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[str]:
    parameters = [
        *node.args.posonlyargs,
        *node.args.args,
        *node.args.kwonlyargs,
    ]
    if node.args.vararg is not None:
        parameters.append(node.args.vararg)
    if node.args.kwarg is not None:
        parameters.append(node.args.kwarg)
    return [parameter.arg for parameter in parameters]


def contains_cache_token(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in CACHE_STATE_TOKENS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    src = case_root / "src"
    service_path = src / "inventory_report_service.py"
    engine_path = src / "summary_engine.py"
    findings: list[str] = []

    for path in (service_path, engine_path):
        if not path.is_file():
            findings.append(f"missing required path: {path.relative_to(case_root)}")
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    trees: dict[Path, ast.Module] = {}
    try:
        for path in sorted(src.rglob("*.py")):
            trees[path] = ast.parse(
                path.read_text(encoding="utf-8"), filename=str(path)
            )
    except (OSError, SyntaxError) as exc:
        print(f"FAIL: could not analyze source files: {exc}")
        return 1

    engine_tree = trees[engine_path]
    for node in ast.walk(engine_tree):
        name: str | None = None
        if isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, ast.Attribute):
            name = node.attr
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
        if name is not None and contains_cache_token(name):
            findings.append(
                "SummaryEngine must remain a pure computation dependency and "
                f"must not own cache state: found '{name}'"
            )
            break

    for path, tree in trees.items():
        relative_path = path.relative_to(case_root)
        for statement in tree.body:
            for name in statement_targets(statement):
                if contains_cache_token(name):
                    findings.append(
                        f"{relative_path}: module-level cache state '{name}' is not allowed"
                    )
            if isinstance(statement, ast.ClassDef):
                for class_statement in statement.body:
                    for name in statement_targets(class_statement):
                        if contains_cache_token(name):
                            findings.append(
                                f"{relative_path}: class-level shared cache state "
                                f"'{statement.name}.{name}' is not allowed"
                            )

    service_tree = trees[service_path]
    service_classes = [
        node
        for node in service_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "InventoryReportService"
    ]
    if len(service_classes) != 1:
        findings.append(
            "inventory_report_service.py must define InventoryReportService exactly once"
        )
    else:
        methods = {
            node.name: node
            for node in service_classes[0].body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for required_method in ("clear_cache", "get_summary"):
            if required_method not in methods:
                findings.append(
                    f"InventoryReportService must continue to expose {required_method}()"
                )
        for method in methods.values():
            bad_parameters = CACHE_CONTROL_PARAMETERS.intersection(
                function_parameters(method)
            )
            if bad_parameters:
                findings.append(
                    "InventoryReportService public API must not grow cache-control "
                    f"parameters: {', '.join(sorted(bad_parameters))}"
                )

    engine_classes = [
        node
        for node in engine_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SummaryEngine"
    ]
    if len(engine_classes) != 1 or not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "compute"
        for node in engine_classes[0].body
    ):
        findings.append("SummaryEngine must continue to expose compute()")

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: cache state and lifecycle controls remain locally owned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
