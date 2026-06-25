#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def has_stats_import(text: str) -> bool:
    return bool(
        re.search(
            r"^\s*(?:import\s+(?:[\w]+\.)*stats\b|from\s+[\w.]+\s+import\s+.*\bstats\b)",
            text,
            re.MULTILINE,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root)
    src_dir = case_root / "src"

    required_paths = [
        src_dir / "submission.py",
        src_dir / "validator.py",
        src_dir / "grader.py",
        src_dir / "reporter.py",
        src_dir / "stats.py",
    ]

    findings: list[str] = []
    for path in required_paths:
        if not path.is_file():
            findings.append(f"missing required path: {path.relative_to(case_root)}")

    validator_path = src_dir / "validator.py"
    if validator_path.is_file():
        validator_text = read_text(validator_path)
        if re.search(r"\btotal_processed\b", validator_text):
            findings.append(
                "validator.py: Validator must not reference total_processed."
            )
        if has_stats_import(validator_text):
            findings.append("validator.py: Validator must not import stats.")

    allowed_total_processed = {
        "stats.py",
        "reporter.py",
    }
    allowed_stats_import = {
        "stats.py",
        "reporter.py",
    }

    for path in src_dir.rglob("*.py"):
        if path.name == "validator.py":
            continue
        text = read_text(path)
        if path.name not in allowed_total_processed and re.search(
            r"\btotal_processed\b", text
        ):
            findings.append(
                f"{path.relative_to(case_root)}: total_processed must stay owned by stats/reporter/main only."
            )
        if path.name not in allowed_stats_import and has_stats_import(text):
            findings.append(
                f"{path.relative_to(case_root)}: stats may only be imported by stats.py, reporter.py, or app/main.py."
            )

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: structural checks succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
