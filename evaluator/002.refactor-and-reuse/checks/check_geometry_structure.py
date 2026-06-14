#!/usr/bin/env python3

"""Structural check for case 002 geometry refactor boundaries.

Rule:
  - Keep only intended file-level modifications for `src/geometry.cc`.
  - Preserve other starter files under `src/` and `app/`.
  - Validate that both fundamental and essential 8-point paths include expected
    numerical-geometry signals.

Inputs:
  - `--case_root` (defaults to script's case root).
  - `--baseline_case_root` (defaults to script location).

Checks:
  - Baseline file drift/new/deleted detection.
  - `EstimateFundamental8Point` and `EstimateEssential8Point` function bodies exist.
  - Presence of normalization and essential-constraint evidence in `src/geometry.cc`.

Output:
  - emit_check_result(passed=<bool>, findings=[diagnostic messages]).
"""

import argparse
from pathlib import Path

from evaluator.shared.path_checks import (
    classify_relative_paths_against_baseline,
    case_root_from_script,
    scan_files,
)
from evaluator.shared.check_output import emit_check_result
from evaluator.shared.source_analysis import (
    count_matching_patterns,
    extract_function_body,
    strip_comments_and_strings,
)


def main() -> int:

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    parser.add_argument(
        "--baseline_case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    baseline_root = args.baseline_case_root.resolve()
    src = case_root / "src" / "geometry.cc"

    current_files = {
        path.relative_to(case_root).as_posix()
        for path in scan_files(
            case_root / "src", case_root / "app", suffixes=(".h", ".cc")
        )
    }

    baseline_files = {
        path.relative_to(baseline_root).as_posix()
        for path in scan_files(
            baseline_root / "src", baseline_root / "app", suffixes=(".h", ".cc")
        )
    }
    tracked_files = sorted(current_files | baseline_files)
    file_status = classify_relative_paths_against_baseline(
        case_root, baseline_root, tracked_files
    )

    findings: list[str] = []
    if file_status.created_in_root:
        findings.append(f"Unexpected new source file: {file_status.created_in_root[0]}")

    if file_status.deleted_from_root:
        findings.append(
            f"Unexpected deleted source file: {file_status.deleted_from_root[0]}"
        )

    forbidden_modifications = [
        path for path in file_status.modified if path != "src/geometry.cc"
    ]
    if forbidden_modifications:
        findings.append(
            f"Unexpected modified protected file: {forbidden_modifications[0]}"
        )

    code = strip_comments_and_strings(src.read_text(encoding="utf-8"))
    fundamental_body = extract_function_body(code, "EstimateFundamental8Point")
    essential_body = extract_function_body(code, "EstimateEssential8Point")

    if not fundamental_body:
        findings.append("Missing EstimateFundamental8Point body")

    if not essential_body:
        findings.append("Missing EstimateEssential8Point body")

    if findings:
        return emit_check_result(passed=False, findings=findings)

    normalization_patterns = [
        r"\bmean_[xy]\b",
        r"\bcentroid\b",
        r"sqrt\s*\(\s*2(?:\.0)?\s*\)",
        r"\bscale\b",
        r"\bT1\b",
        r"\bT2\b",
        r"transpose\s*\(\s*\)\s*\*.*\*",
    ]

    normalization_hits = count_matching_patterns(normalization_patterns, code)
    if normalization_hits < 3:
        findings.append(
            "Expected Hartley-style normalization evidence in src/geometry.cc"
        )

    essential_constraint_patterns = [
        r"\w+\s*\(\s*0\s*\)\s*=\s*\w+\s*\(\s*1\s*\)",
        r"\w+\s*\(\s*1\s*\)\s*=\s*\w+\s*\(\s*0\s*\)",
        r"\w+\s*\[\s*0\s*\]\s*=\s*\w+\s*\[\s*1\s*\]",
        r"\w+\s*\[\s*1\s*\]\s*=\s*\w+\s*\[\s*0\s*\]",
        r"(?:Vector3d|Diagonal|DiagonalMatrix)\s*\(\s*1(?:\.0)?\s*,\s*1(?:\.0)?\s*,\s*0(?:\.0)?\s*\)",
        r"\bJacobiSVD\b[\s\S]*?\bsingularValues\b",
        r"\bsingularValues\b.*=.*\b1(?:\.0)?\s*,\s*1(?:\.0)?\s*,\s*0(?:\.0)?",
        r"\b\w+\s*<<\s*\w+\s*,\s*\w+\s*,\s*0(?:\.0)?\b",
        r"\b\w+\s*=\s*0\.5\s*\*\s*\(\s*\w+\s*\(\s*0\s*\)\s*\+\s*\w+\s*\(\s*1\s*\)\s*\)",
    ]

    essential_hits = count_matching_patterns(essential_constraint_patterns, code)
    if essential_hits == 0:
        findings.append(
            "Expected essential-matrix singular value constraint handling in src/geometry.cc"
        )

    if "return Solve8Point" in essential_body and essential_hits == 0:
        findings.append(
            "Essential path appears to reuse the fundamental solve without essential-specific post-processing"
        )
    return emit_check_result(passed=not findings, findings=findings)


if __name__ == "__main__":
    raise SystemExit(main())
