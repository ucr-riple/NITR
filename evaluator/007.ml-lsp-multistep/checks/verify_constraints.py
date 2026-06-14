#!/usr/bin/env python3

"""Verify generic-transform constraints for case 007 multi-step pipeline.

Rule:
  - Keep protected files (`feature_pipeline.*`, `feature_transform.h`) unchanged
    versus baseline.
  - Require required transform artifacts to exist.
  - Forbid RTTI-like constructs (`dynamic_cast`, `typeid`) in `src`.
  - Prevent concrete transform-type leakage inside generic transform pipeline files.

Inputs:
  - `--case_root` (defaults to case root inferred from script path).
  - `--baseline_case_root` (defaults to same inferred case root).

Output:
  - emit_check_result(passed=<bool>, findings=[diagnostic messages]).
"""

import argparse
from pathlib import Path

from evaluator.shared.path_checks import (
    classify_relative_paths_against_baseline,
    case_root_from_script,
    find_missing_paths,
    find_missing_relative_paths,
    read_text,
    scan_files,
)
from evaluator.shared.source_analysis import find_matching_substrings
from evaluator.shared.check_output import emit_check_result

PROTECTED_FILES = [
    "src/feature_transform.h",
    "src/feature_pipeline.h",
    "src/feature_pipeline.cc",
]

REQUIRED_FILES = [
    "src/clamp_transform.h",
    "src/clamp_transform.cc",
    "src/transform_batch.h",
    "src/transform_batch.cc",
    "src/transform_chain.h",
    "src/transform_chain.cc",
]

FORBIDDEN_PATTERNS = [
    "dynamic_cast",
    "typeid",
]

GENERIC_FILES = [
    "src/transform_batch.h",
    "src/transform_batch.cc",
    "src/transform_chain.h",
    "src/transform_chain.cc",
]

CONCRETE_TOKENS = [
    "ClampTransform",
    "IdentityTransform",
    "L2NormalizeTransform",
]


def main() -> int:
    """Validate protected files, required artifacts, and generic pipeline boundaries."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root", type=Path, default=case_root_from_script(__file__)
    )
    parser.add_argument(
        "--baseline_case_root", type=Path, default=case_root_from_script(__file__)
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    baseline_root = args.baseline_case_root.resolve()

    findings: list[str] = []
    for rel in find_missing_relative_paths(case_root, REQUIRED_FILES):
        findings.append(f"missing required file: {rel}")

    protected_status = classify_relative_paths_against_baseline(
        case_root, baseline_root, PROTECTED_FILES
    )
    for rel in protected_status.missing_in_root:
        findings.append(f"missing protected file: {rel}")

    for rel in protected_status.missing_in_baseline:
        findings.append(f"missing baseline protected file: {rel}")

    for rel in protected_status.modified:
        findings.append(f"protected file modified: {rel}")
    for path in scan_files(case_root / "src", suffixes=(".h", ".cc")):
        text = read_text(path, missing_ok=False)
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in text:
                findings.append(
                    f"forbidden pattern {pattern} found in {path.relative_to(case_root)}"
                )
    for rel in GENERIC_FILES:
        path = case_root / rel
        if find_missing_paths([path]):
            continue
        text = read_text(path, missing_ok=False)
        for token in find_matching_substrings(CONCRETE_TOKENS, text):
            findings.append(f"generic path leaked concrete type {token} in {rel}")
    return emit_check_result(passed=not findings, findings=findings)


if __name__ == "__main__":
    raise SystemExit(main())
