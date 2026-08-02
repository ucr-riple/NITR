#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from pathlib import Path

FORBIDDEN_RESULT_FIELDS = {
    "status",
    "lost_on_tie_break",
    "tie_break_against_id",
    "winner_id",
    "loser_id",
    "decided_by_tie_break",
    "decisive_reason",
}
LOG_METHODS = {"debug", "info", "warning", "error", "critical", "log"}


def parse_source(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def non_executable_string_nodes(tree: ast.Module) -> set[int]:
    excluded: set[int] = set()
    owners = [
        node
        for node in ast.walk(tree)
        if isinstance(
            node,
            (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
        )
    ]
    for owner in owners:
        if not owner.body:
            continue
        first = owner.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            excluded.add(id(first.value))

    for node in ast.walk(tree):
        annotations: list[ast.AST] = []
        if isinstance(node, ast.arg) and node.annotation is not None:
            annotations.append(node.annotation)
        elif isinstance(node, ast.AnnAssign):
            annotations.append(node.annotation)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                annotations.append(node.returns)
        for annotation in annotations:
            excluded.update(id(child) for child in ast.walk(annotation))
    return excluded


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()
    source_root = Path(args.case_root).resolve() / "src"
    findings: list[str] = []

    try:
        ranker_tree = parse_source(source_root / "ranker.py")
        models_tree = parse_source(source_root / "models.py")
    except (OSError, SyntaxError) as exc:
        print(f"FAIL: could not analyze ranking source: {exc}")
        return 1

    excluded_strings = non_executable_string_nodes(ranker_tree)
    for node in ast.walk(ranker_tree):
        is_print = (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        )
        is_log = (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in LOG_METHODS
        )
        if is_print or is_log:
            findings.append(
                "ranking core must not emit display, logging, or tracing output"
            )
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in excluded_strings
        ):
            if node.value:
                findings.append(
                    "ranking core should not contain executable explanation-oriented strings"
                )

    ranked_classes = [
        node
        for node in models_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "RankedItem"
    ]
    if len(ranked_classes) != 1:
        findings.append("models.py must define RankedItem exactly once")
    else:
        fields = [
            node.target.id
            for node in ranked_classes[0].body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        ]
        if len(fields) > 3:
            findings.append(
                "RankedItem should remain compact with at most three fields"
            )
        leaked = FORBIDDEN_RESULT_FIELDS.intersection(fields)
        if leaked:
            findings.append(
                "inspection/comparison fields leaked into RankedItem: "
                + ", ".join(sorted(leaked))
            )

    if findings:
        for finding in dict.fromkeys(findings):
            print(f"FAIL: {finding}")
        return 1

    print("PASS: observer features remain outside the compact ranking path")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
