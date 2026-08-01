#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from pathlib import Path

GENERIC_PATHS = ("src/transform_batch.py", "src/transform_chain.py")
CONCRETE_NAMES = {
    "ClampTransform",
    "IdentityTransform",
    "L2NormalizeTransform",
    "clamp_transform",
    "identity_transform",
    "l2_normalize_transform",
}


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()
    case_root = Path(args.case_root).resolve()
    findings: list[str] = []
    trees: dict[str, ast.Module] = {}

    for relative in GENERIC_PATHS:
        path = case_root / relative
        if not path.is_file():
            findings.append(f"missing required path: {relative}")
            continue
        try:
            trees[relative] = parse(path)
        except (OSError, SyntaxError) as exc:
            findings.append(f"could not analyze {relative}: {exc}")

    for relative, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in CONCRETE_NAMES:
                findings.append(f"generic path leaked concrete type in {relative}")
            if isinstance(node, ast.Attribute) and node.attr in CONCRETE_NAMES:
                findings.append(f"generic path leaked concrete type in {relative}")
            if isinstance(node, ast.Constant) and node.value in CONCRETE_NAMES:
                findings.append(f"generic path dispatched on concrete type in {relative}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"isinstance", "issubclass", "type"}:
                    findings.append(
                        f"generic path used concrete-type inspection in {relative}"
                    )
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                else:
                    names = [node.module or ""] + [alias.name for alias in node.names]
                if any(part in CONCRETE_NAMES for name in names for part in name.split(".")):
                    findings.append(f"generic path imported concrete transform in {relative}")

    batch_tree = trees.get("src/transform_batch.py")
    if batch_tree is not None and not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "transform"
        for node in ast.walk(batch_tree)
    ):
        findings.append("transform_batch() must call the shared transform() contract")

    chain_tree = trees.get("src/transform_chain.py")
    if chain_tree is not None:
        chain_classes = [
            node
            for node in chain_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "TransformChain"
        ]
        if len(chain_classes) != 1 or not any(
            isinstance(base, ast.Name) and base.id == "FeatureTransform"
            for base in (chain_classes[0].bases if chain_classes else [])
        ):
            findings.append("TransformChain must implement FeatureTransform")
        if not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "transform"
            for node in ast.walk(chain_tree)
        ):
            findings.append("TransformChain must compose the shared transform() contract")

    if findings:
        for finding in dict.fromkeys(findings):
            print(f"FAIL: {finding}")
        return 1
    print("PASS: batch and chain callers remain generic and substitutable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
