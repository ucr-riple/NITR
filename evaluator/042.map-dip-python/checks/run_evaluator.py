#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from pathlib import Path

CONCRETE_NAMES = {"GeometryProvider", "SemanticsProvider"}
BUILTIN_TYPES = {"geometry", "semantics", "reverse_payload"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()
    path = Path(args.case_root).resolve() / "src" / "map_snapshot.py"
    if not path.is_file():
        print("FAIL: missing required path: src/map_snapshot.py")
        return 1
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        print(f"FAIL: could not analyze src/map_snapshot.py: {exc}")
        return 1

    findings: list[str] = []
    service_classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "MapSnapshotService"
    ]
    methods = [
        node
        for service in service_classes
        for node in service.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "build_snapshot"
    ]
    if len(methods) != 1:
        findings.append("MapSnapshotService must define build_snapshot() exactly once")
    else:
        method = methods[0]
        arguments = method.args
        if (
            [argument.arg for argument in arguments.args]
            != ["self", "config", "payload"]
            or arguments.posonlyargs
            or arguments.kwonlyargs
            or arguments.vararg is not None
            or arguments.kwarg is not None
            or arguments.defaults
            or arguments.kw_defaults
        ):
            findings.append(
                "MapSnapshotService.build_snapshot() public signature changed"
            )
        for node in ast.walk(method):
            if isinstance(node, ast.Name) and node.id in CONCRETE_NAMES:
                findings.append(f"snapshot core references concrete provider {node.id}")
            if isinstance(node, ast.Attribute) and node.attr in CONCRETE_NAMES:
                findings.append(
                    f"snapshot core references concrete provider {node.attr}"
                )
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value in BUILTIN_TYPES
            ):
                findings.append(
                    f"snapshot core contains provider-specific type: {node.value}"
                )
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imported = [alias.name for alias in node.names]
                if any(name in CONCRETE_NAMES for name in imported):
                    findings.append("snapshot core imports concrete providers")
        uses_registry = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create"
            for node in ast.walk(method)
        )
        if not uses_registry:
            findings.append("build_snapshot() must create layers through a registry")

    if findings:
        for finding in dict.fromkeys(findings):
            print(f"FAIL: {finding}")
        return 1
    print("PASS: snapshot policy depends on the provider registry abstraction")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
