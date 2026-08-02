#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from pathlib import Path

CONCRETE_PROVIDERS = {"StaticPolicyProvider", "FilePolicyProvider"}
SELECTION_DETAILS = {"policy_mode", "policy_file_path", "build_pipeline"}
WIRING_EXEMPT_FILES = {
    "build_pipeline.py",
    "static_policy_provider.py",
    "file_policy_provider.py",
}


def parse_source(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def referenced_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    source_root = case_root / "src"
    findings: list[str] = []

    runner_path = source_root / "pipeline_runner.py"
    try:
        runner_tree = parse_source(runner_path)
    except (OSError, SyntaxError) as exc:
        print(f"FAIL: could not analyze src/pipeline_runner.py: {exc}")
        return 1

    for node in ast.walk(runner_tree):
        name = referenced_name(node)
        if name in CONCRETE_PROVIDERS:
            findings.append(
                f"PipelineRunner depends on concrete provider {name}"
            )
        if name in SELECTION_DETAILS:
            findings.append(
                f"PipelineRunner leaks provider selection detail: {name}"
            )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in CONCRETE_PROVIDERS
        ):
            findings.append("PipelineRunner constructs a concrete provider")

    boundary_path = source_root / "build_pipeline.py"
    try:
        boundary_tree = parse_source(boundary_path)
    except (OSError, SyntaxError) as exc:
        findings.append(f"could not analyze build_pipeline.py: {exc}")
        boundary_tree = ast.Module(body=[], type_ignores=[])

    boundary_names = {
        node.id for node in ast.walk(boundary_tree) if isinstance(node, ast.Name)
    }
    for provider_name in CONCRETE_PROVIDERS:
        if provider_name not in boundary_names:
            findings.append(
                f"composition boundary must wire {provider_name}"
            )

    for path in source_root.glob("*.py"):
        if path.name in WIRING_EXEMPT_FILES:
            continue
        source = path.read_text(encoding="utf-8")
        for provider_name in CONCRETE_PROVIDERS:
            if provider_name in source:
                findings.append(
                    "concrete provider wiring escaped boundary into "
                    f"src/{path.name}"
                )

    if findings:
        for finding in dict.fromkeys(findings):
            print(f"FAIL: {finding}")
        return 1

    print("PASS: provider selection remains in the composition boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
