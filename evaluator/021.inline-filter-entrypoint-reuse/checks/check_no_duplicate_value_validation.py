#!/usr/bin/env python3

from evaluator.shared.check_utils import (
    case_root_from_script,
    has_all_substrings,
    has_any_substring,
    scan_files,
)

ALLOWED_FILES = {"filter_validation.cc", "filter_validation.h"}


def main() -> int:
    """Reject duplicate numeric value validation outside the shared validation module."""
    src_dir = case_root_from_script(__file__) / "src"
    for source_file in scan_files(src_dir, suffixes=(".h", ".cc", ".cpp")):
        if source_file.name in ALLOWED_FILES:
            continue

        content = source_file.read_text(encoding="utf-8", errors="replace")

        if has_any_substring(["std::stoi", "std::isdigit"], content):
            print(
                f"Suspicious duplicate numeric validation outside filter_validation: {source_file}"
            )
            return 1

        if has_all_substrings(
            ["FilterValueKind::kInteger", "ParseInlineFilter"], content
        ):
            print(
                f"Suspicious inline-only rule construction with integer value handling in {source_file}"
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
