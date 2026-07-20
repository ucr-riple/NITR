#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from pathlib import Path

EXPECTED_BOOK_FIELDS = ["id", "title", "author", "archived"]
EXPECTED_METHOD_PARAMETERS = {
    "find_available_titles": ["self", "books", "prefix"],
    "build_catalog_digest": ["self", "books"],
}
FORBIDDEN_CONTROL_NAMES = {
    "include_archived",
    "show_archived",
    "archived_mode",
    "includeArchived",
}


def function_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[str]:
    return [
        parameter.arg
        for parameter in [
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        ]
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    catalog_path = case_root / "src" / "library_catalog.py"
    if not catalog_path.is_file():
        print("FAIL: missing required path: src/library_catalog.py")
        return 1

    try:
        tree = ast.parse(
            catalog_path.read_text(encoding="utf-8"), filename=str(catalog_path)
        )
    except (OSError, SyntaxError) as exc:
        print(f"FAIL: could not analyze src/library_catalog.py: {exc}")
        return 1

    findings: list[str] = []
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

    book_class = classes.get("Book")
    if book_class is None:
        findings.append("public Book type is missing")
    else:
        book_fields = [
            node.target.id
            for node in book_class.body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        ]
        if book_fields != EXPECTED_BOOK_FIELDS:
            findings.append(
                "public Book fields changed unexpectedly: expected "
                + ", ".join(EXPECTED_BOOK_FIELDS)
            )

    service_class = classes.get("CatalogService")
    if service_class is None:
        findings.append("public CatalogService type is missing")
    else:
        public_methods = {
            node.name: node
            for node in service_class.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
        }
        if set(public_methods) != set(EXPECTED_METHOD_PARAMETERS):
            findings.append(
                "CatalogService public method set changed unexpectedly: expected "
                + ", ".join(EXPECTED_METHOD_PARAMETERS)
            )

        for method_name, expected_parameters in EXPECTED_METHOD_PARAMETERS.items():
            method = public_methods.get(method_name)
            if method is None:
                continue
            parameters = function_parameters(method)
            has_variadic = (
                method.args.vararg is not None or method.args.kwarg is not None
            )
            has_defaults = bool(method.args.defaults or method.args.kw_defaults)
            if parameters != expected_parameters or has_variadic or has_defaults:
                findings.append(
                    f"public API signature changed unexpectedly: {method_name}()"
                )

        for node in ast.walk(service_class):
            name: str | None = None
            if isinstance(node, ast.Name):
                name = node.id
            elif isinstance(node, ast.Attribute):
                name = node.attr
            elif isinstance(node, ast.arg):
                name = node.arg
            if name in FORBIDDEN_CONTROL_NAMES:
                findings.append(f"forbidden public API control flag detected: {name}")
                break

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: catalog public API remains stable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
