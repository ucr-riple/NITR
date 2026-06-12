#!/usr/bin/env python3

from pathlib import Path

from evaluator.shared.check_utils import has_all_substrings, has_any_substring


CASE_REL = Path("cases/021.inline-filter-entrypoint-reuse/src")
ALLOWED_FILES = {"filter_validation.cc", "filter_validation.h"}


def main() -> int:
    """Reject duplicate numeric value validation outside the shared validation module."""
    workspace_root = Path.cwd()
    src_dir = workspace_root / CASE_REL
    for source_file in sorted(src_dir.glob("*.[ch]c*")):
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
