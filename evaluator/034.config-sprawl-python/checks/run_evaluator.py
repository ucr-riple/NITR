#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from pathlib import Path


class SignatureScanner(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.class_names: list[str] = []
        self.findings: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_names.append(node.name)
        self.generic_visit(node)
        self.class_names.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        parameters = [
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        ]
        if node.args.vararg is not None:
            parameters.append(node.args.vararg)
        if node.args.kwarg is not None:
            parameters.append(node.args.kwarg)

        if any(parameter.arg == "compact_mode" for parameter in parameters):
            qualname = ".".join([*self.class_names, node.name])
            self.findings.append(
                f"{self.path}: standalone compact_mode parameter in function "
                f"signature: {qualname}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    src = case_root / "src"
    renderer_path = src / "report_renderer.py"
    if not renderer_path.is_file():
        print("FAIL: missing required path: src/report_renderer.py")
        return 1

    findings: list[str] = []
    for path in sorted(src.rglob("*.py")):
        relative_path = path.relative_to(case_root)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            print(f"FAIL: could not analyze {relative_path}: {exc}")
            return 1

        scanner = SignatureScanner(relative_path)
        scanner.visit(tree)
        findings.extend(scanner.findings)

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: ReportOptions remains the renderer configuration boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
