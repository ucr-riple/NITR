#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_parse_inline_body(text: str) -> str | None:
    match = re.search(
        r"^def parse_inline_filter\(.*?\)[^\n]*:\n((?:^[ \t]+.*\n?|^\n)*)",
        text,
        flags=re.MULTILINE,
    )
    if match is None:
        return None
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root)
    src_dir = case_root / "src"
    required_paths = [
        src_dir / "filter_clause.py",
        src_dir / "filter_rule.py",
        src_dir / "filter_parser.py",
        src_dir / "filter_validation.py",
    ]

    findings: list[str] = []
    for path in required_paths:
        if not path.is_file():
            findings.append(f"missing required path: {path.relative_to(case_root)}")

    parser_path = src_dir / "filter_parser.py"
    validation_path = src_dir / "filter_validation.py"
    if parser_path.is_file():
        parser_text = read_text(parser_path)
        if "parse_filter_clause(" not in parser_text:
            findings.append(
                "filter_parser.py: parse_inline_filter must reuse parse_filter_clause."
            )

        inline_body = find_parse_inline_body(parser_text)
        if inline_body is None:
            findings.append("filter_parser.py: missing parse_inline_filter definition.")
        else:
            if "FilterRule(" in inline_body:
                findings.append(
                    "filter_parser.py: parse_inline_filter must not construct FilterRule directly."
                )
            if re.search(
                r"\bFilterErrorCode\.(INVALID_FIELD|INVALID_OPERATOR)\b", inline_body
            ):
                findings.append(
                    "filter_parser.py: parse_inline_filter must not classify invalid field/operator locally."
                )
            if re.search(r"\bint\s*\(", inline_body):
                findings.append(
                    "filter_parser.py: parse_inline_filter must not parse typed values directly."
                )
            field_hits = sum(
                name in inline_body for name in ['"status"', '"priority"', '"owner"']
            )
            if field_hits >= 2:
                findings.append(
                    "filter_parser.py: parse_inline_filter appears to duplicate supported-field interpretation."
                )

    for path in src_dir.glob("*.py"):
        if path.name in {"filter_validation.py", "filter_rule.py"}:
            continue
        text = read_text(path)
        bad_error_hits = sum(
            token in text
            for token in [
                "FilterErrorCode.INVALID_FIELD",
                "FilterErrorCode.INVALID_OPERATOR",
            ]
        )
        if bad_error_hits >= 2:
            findings.append(
                f"{path.relative_to(case_root)}: suspicious duplicate error classification outside validation."
            )

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: structural checks succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
