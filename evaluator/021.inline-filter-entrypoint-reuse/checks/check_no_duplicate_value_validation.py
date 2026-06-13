#!/usr/bin/env python3

import argparse
from pathlib import Path

from evaluator.shared.path_checks import (
    case_root_from_script,
    scan_files,
)
from evaluator.shared.source_analysis import has_all_substrings, has_any_substring
from evaluator.shared.check_output import emit_check_result

ALLOWED_FILES = {"filter_validation.cc", "filter_validation.h"}


def main() -> int:
    """Reject duplicate numeric value validation outside the shared validation module."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    src_dir = case_root / "src"

    for source_file in scan_files(src_dir, suffixes=(".h", ".cc", ".cpp")):
        if source_file.name in ALLOWED_FILES:
            continue

        content = source_file.read_text(encoding="utf-8", errors="replace")

        if has_any_substring(["std::stoi", "std::isdigit"], content):
            return emit_check_result(
                passed=False,
                findings=[
                    f"Suspicious duplicate numeric validation outside filter_validation: {source_file}"
                ],
            )

        if has_all_substrings(
            ["FilterValueKind::kInteger", "ParseInlineFilter"], content
        ):
            return emit_check_result(
                passed=False,
                findings=[
                    f"Suspicious inline-only rule construction with integer value handling in {source_file}"
                ],
            )

    return emit_check_result(passed=True, findings=[])


if __name__ == "__main__":
    raise SystemExit(main())
