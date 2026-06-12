#!/usr/bin/env python3

from pathlib import Path

from evaluator.shared.check_utils import count_matching_substrings, has_any_substring


CASE_REL = Path("cases/021.inline-filter-entrypoint-reuse/src")
ALLOWED_FILES = {"filter_validation.cc", "filter_validation.h", "filter_rule.cc"}
FIELD_LITERALS = ['"status"', '"priority"', '"owner"']
ERROR_LITERALS = [
    "FilterErrorCode::kInvalidField",
    "FilterErrorCode::kInvalidOperator",
    "FilterErrorCode::kInvalidValue",
]


def main() -> int:
    """Reject duplicated field/error lookup tables outside the shared validation layer."""
    workspace_root = Path.cwd()
    src_dir = workspace_root / CASE_REL
    for source_file in sorted(src_dir.glob("*.[ch]c*")):
        if source_file.name in ALLOWED_FILES:
            continue

        content = source_file.read_text(encoding="utf-8", errors="replace")
        field_hits = count_matching_substrings(FIELD_LITERALS, content)
        error_hits = count_matching_substrings(ERROR_LITERALS, content)
        has_inline_parser = has_any_substring(["ParseInlineFilter"], content)

        if field_hits > 1:
            print(
                f"Suspicious duplicated field interpretation outside filter_validation: {source_file}"
            )
            return 1

        if has_inline_parser and field_hits > 0 and error_hits > 1:
            print(
                f"Suspicious duplicated error classification outside filter_validation: {source_file}"
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
