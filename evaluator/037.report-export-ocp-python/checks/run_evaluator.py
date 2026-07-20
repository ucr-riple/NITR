#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from pathlib import Path


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


def class_methods(node: ast.ClassDef) -> set[str]:
    return {
        child.name
        for child in node.body
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    src = case_root / "src"
    service_path = src / "report_export_service.py"
    factory_path = src / "exporter_factory.py"
    findings: list[str] = []

    for path in (service_path, factory_path):
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

    service_tree = trees[service_path]
    for node in ast.walk(service_tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            lowered = node.value.lower()
            if "markdown" in lowered or lowered == "md":
                findings.append(
                    "ReportExportService must remain format-agnostic and must "
                    "not contain Markdown-specific values"
                )
                break
        name: str | None = None
        if isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, ast.Attribute):
            name = node.attr
        if name is not None and "markdown" in name.lower():
            findings.append(
                "ReportExportService must not depend directly on the Markdown "
                f"exporter implementation: found {name}"
            )
            break

    markdown_classes: list[tuple[Path, ast.ClassDef]] = []
    for path, tree in trees.items():
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "MarkdownReportExporter":
                markdown_classes.append((path, node))

    if len(markdown_classes) != 1:
        findings.append(
            "exactly one MarkdownReportExporter extension must be defined under src/"
        )
    else:
        path, markdown_class = markdown_classes[0]
        base_names = {dotted_name(base) for base in markdown_class.bases}
        if "ReportExporter" not in base_names:
            findings.append(
                f"{path.relative_to(case_root)}: MarkdownReportExporter must "
                "extend ReportExporter"
            )
        missing_methods = {"can_handle", "export"} - class_methods(markdown_class)
        if missing_methods:
            findings.append(
                "MarkdownReportExporter must implement: "
                + ", ".join(sorted(missing_methods))
            )

    factory_tree = trees[factory_path]
    factory_functions = [
        node
        for node in factory_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "create_default_exporters"
    ]
    if len(factory_functions) != 1:
        findings.append("exporter factory must define create_default_exporters()")
    elif not any(
        isinstance(node, ast.Call)
        and dotted_name(node.func) == "MarkdownReportExporter"
        for node in ast.walk(factory_functions[0])
    ):
        findings.append(
            "create_default_exporters() must register MarkdownReportExporter"
        )

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: Markdown export uses the existing exporter extension seam")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
