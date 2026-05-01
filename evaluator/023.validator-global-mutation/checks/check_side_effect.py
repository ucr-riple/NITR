#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def strip_comments_and_strings(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    text = re.sub(r"'(?:\\.|[^'\\])+'", "''", text)
    return text


def include_paths(text: str) -> list[str]:
    includes: list[str] = []
    for line in text.splitlines():
        match = re.match(r'^\s*#\s*include\s*[<"]([^">]+)[">]', line)
        if match:
            includes.append(match.group(1))
    return includes


def main() -> int:
    if len(sys.argv) > 1:
        case_root = Path(sys.argv[1]).resolve()
    else:
        repo_root = Path(__file__).resolve().parents[3]
        case_root = repo_root / "cases" / "023.validator-global-mutation"

    src_root = case_root / "src"
    validator_files = [
        src_root / "validator.h",
        src_root / "validator.cc",
    ]

    failures: list[str] = []

    for path in validator_files:
        raw_text = read_text(path)
        if not raw_text:
            failures.append(f"{path.name}: missing or unreadable validator file.")
            continue

        scanned_text = strip_comments_and_strings(raw_text)
        includes = include_paths(raw_text)

        if any(include.endswith("stats.h") for include in includes):
            failures.append(
                f"{path.name}: Validator must not include stats.h directly."
            )

        if any(include.startswith("src/") for include in includes):
            failures.append(
                f'{path.name}: do not use #include "src/..."; keep starter relative '
                "include style."
            )

        if re.search(r"\btotal_processed\b", scanned_text):
            failures.append(
                f"{path.name}: Validator must not reference total_processed."
            )

    if failures:
        print("Maintainability check failed:")
        for failure in failures:
            print(f"- {failure}")
        print(
            "Validator should only inspect Submission and return a boolean. "
            "The total_processed counter belongs in app/main.cc, not inside "
            "the validation files."
        )
        return 1

    print(
        "Side-effect check passed: Validator remains decoupled from global stats."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
