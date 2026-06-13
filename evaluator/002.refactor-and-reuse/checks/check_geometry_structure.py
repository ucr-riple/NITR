#!/usr/bin/env python3

import argparse
import pathlib

from evaluator.shared.path_checks import (
    classify_relative_paths_against_baseline,
    case_root_from_script,
    scan_files,
)
from evaluator.shared.source_analysis import (
    count_matching_patterns,
    extract_function_body,
    strip_comments_and_strings,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=pathlib.Path,
        default=case_root_from_script(__file__),
    )
    parser.add_argument(
        "--baseline_case_root",
        type=pathlib.Path,
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

    if file_status.created_in_root:
        print(f"Unexpected new source file: {file_status.created_in_root[0]}")
        return 1

    if file_status.deleted_from_root:
        print(f"Unexpected deleted source file: {file_status.deleted_from_root[0]}")
        return 1

    forbidden_modifications = [
        path for path in file_status.modified if path != "src/geometry.cc"
    ]
    if forbidden_modifications:
        print(f"Unexpected modified protected file: {forbidden_modifications[0]}")
        return 1

    code = strip_comments_and_strings(src.read_text(encoding="utf-8"))
    fundamental_body = extract_function_body(code, "EstimateFundamental8Point")
    essential_body = extract_function_body(code, "EstimateEssential8Point")

    if not fundamental_body:
        print("Missing EstimateFundamental8Point body")
        return 1

    if not essential_body:
        print("Missing EstimateEssential8Point body")
        return 1

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
        print("Expected Hartley-style normalization evidence in src/geometry.cc")
        return 1

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
        print(
            "Expected essential-matrix singular value constraint handling in src/geometry.cc"
        )
        return 1

    if "return Solve8Point" in essential_body and essential_hits == 0:
        print(
            "Essential path appears to reuse the fundamental solve without essential-specific post-processing"
        )
        return 1

    print("geometry structure checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
