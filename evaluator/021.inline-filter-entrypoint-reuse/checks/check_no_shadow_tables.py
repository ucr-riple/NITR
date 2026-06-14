#!/usr/bin/env python3

"""Reject duplicated filter shadow tables outside the shared validation module.

Rule:
  - Disallow repeated field/error lookup/table patterns in non-validation files.
  - Ensure field constants and error mapping helpers are centralized.

Inputs:
  - `--case_root` (defaults to script's case root).
  - All source files under `src/` (except allowed validation files).

Output:
  - emit_check_result(passed=<bool>, findings=[offending path and reason]).
"""

import argparse
from pathlib import Path

from evaluator.shared.path_checks import (
    case_root_from_script,
    scan_files,
)
from evaluator.shared.source_analysis import (
    count_matching_substrings,
    has_any_substring,
)
from evaluator.shared.check_output import emit_check_result

ALLOWED_FILES = {"filter_validation.cc", "filter_validation.h", "filter_rule.cc"}
FIELD_LITERALS = ['"status"', '"priority"', '"owner"']
ERROR_LITERALS = [
    "FilterErrorCode::kInvalidField",
    "FilterErrorCode::kInvalidOperator",
    "FilterErrorCode::kInvalidValue",
]


def main() -> int:
    """Reject duplicated field/error lookup tables outside the shared validation layer."""
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
        field_hits = count_matching_substrings(FIELD_LITERALS, content)
        error_hits = count_matching_substrings(ERROR_LITERALS, content)
        has_inline_parser = has_any_substring(["ParseInlineFilter"], content)

        if field_hits > 1:
            return emit_check_result(
                passed=False,
                findings=[
                    f"Suspicious duplicated field interpretation outside filter_validation: {source_file}"
                ],
            )

        if has_inline_parser and field_hits > 0 and error_hits > 1:
            return emit_check_result(
                passed=False,
                findings=[
                    f"Suspicious duplicated error classification outside filter_validation: {source_file}"
                ],
            )

    return emit_check_result(passed=True, findings=[])


if __name__ == "__main__":
    raise SystemExit(main())
