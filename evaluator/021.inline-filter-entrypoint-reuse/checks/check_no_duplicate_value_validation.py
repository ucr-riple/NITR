#!/usr/bin/env python3

from pathlib import Path
import sys


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
        has_stoi = "std::stoi" in content
        has_isdigit = "std::isdigit" in content
        has_integer_value = "FilterValueKind::kInteger" in content
        has_inline_parser = "ParseInlineFilter" in content

        if has_stoi or has_isdigit:
            print(f"Suspicious duplicate numeric validation outside filter_validation: {source_file}")
            return 1

        if has_integer_value and has_inline_parser:
            print(
                f"Suspicious inline-only rule construction with integer value handling in {source_file}"
            )
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
