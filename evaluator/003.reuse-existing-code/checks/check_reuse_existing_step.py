#!/usr/bin/env python3

import argparse
import re
from pathlib import Path

from evaluator.shared.check_output import emit_check_result, fail_message
from evaluator.shared.path_checks import (
    case_root_from_script,
    classify_relative_paths_against_baseline,
    read_text,
    scan_files,
)


def main() -> int:
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

    current_files = {
        path.relative_to(case_root).as_posix()
        for path in scan_files(case_root / "src", suffixes=(".h", ".cc"))
    }
    baseline_files = {
        path.relative_to(baseline_root).as_posix()
        for path in scan_files(baseline_root / "src", suffixes=(".h", ".cc"))
    }
    tracked_files = sorted(current_files | baseline_files)
    file_status = classify_relative_paths_against_baseline(
        case_root, baseline_root, tracked_files
    )

    if file_status.created_in_root:
        return fail_message(
            f"Unexpected new source file: {file_status.created_in_root[0]}"
        )

    if file_status.deleted_from_root:
        return fail_message(
            f"Unexpected deleted source file: {file_status.deleted_from_root[0]}"
        )

    forbidden_modifications = [
        path for path in file_status.modified if path != "src/cosine_similarity.cc"
    ]
    if forbidden_modifications:
        return fail_message(
            f"Unexpected modified protected file: {forbidden_modifications[0]}"
        )

    path = case_root / "src" / "cosine_similarity.cc"
    code = read_text(path)
    if not code:
        return fail_message(f"Failed to read {path}")

    required_patterns = {
        '#include "dot_product.h"': re.compile(r'#include\s+"dot_product\.h"'),
        '#include "l2_norm.h"': re.compile(r'#include\s+"l2_norm\.h"'),
        "DotProduct(...) call": re.compile(r"(?:nitr::case003::)?DotProduct\s*\("),
        "L2Norm(...) call": re.compile(r"(?:nitr::case003::)?L2Norm\s*\("),
    }
    for description, pattern in required_patterns.items():
        if not pattern.search(code):
            return fail_message(
                f"Structural reuse check failed: missing {description} in src/cosine_similarity.cc"
            )

    forbidden_patterns = [
        re.compile(r"\bsqrt\s*\("),
        re.compile(r"sum_sq\s*\+="),
        re.compile(r"sum\s*\+=\s*[^;]*\*[^;]*;"),
    ]
    if any(pattern.search(code) for pattern in forbidden_patterns):
        return fail_message(
            "Structural check failed: detected likely re-implementation of math utilities in src/cosine_similarity.cc"
        )

    return emit_check_result(passed=True, findings=[])


if __name__ == "__main__":
    raise SystemExit(main())
