#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from evaluator.shared.path_checks import (
    case_root_from_script,
    classify_relative_paths_against_baseline,
    read_text,
    scan_files,
)
from evaluator.shared.check_output import emit_check_result
from evaluator.shared.source_analysis import (
    has_any_pattern,
    include_paths,
    strip_comments_and_strings,
)

PROTECTED_FILES = [
    "app/main.cc",
    "src/grader.cc",
    "src/reporter.cc",
]


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

    src_root = case_root / "src"
    app_root = case_root / "app"
    validator_files = [
        src_root / "validator.h",
        src_root / "validator.cc",
    ]
    allowed_total_processed_refs = {
        src_root / "stats.h",
        src_root / "stats.cc",
        src_root / "reporter.cc",
        app_root / "main.cc",
    }
    allowed_stats_includes = {
        src_root / "stats.cc",
        src_root / "reporter.cc",
        app_root / "main.cc",
    }

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

        if has_any_pattern([r"\btotal_processed\b"], scanned_text):
            failures.append(
                f"{path.name}: Validator must not reference total_processed."
            )

    source_files = scan_files(src_root, suffixes=(".h", ".cc"))
    source_files.append(app_root / "main.cc")
    for path in source_files:
        raw_text = read_text(path)
        if not raw_text:
            failures.append(
                f"{path.relative_to(case_root)}: missing or unreadable file."
            )
            continue

        scanned_text = strip_comments_and_strings(raw_text)
        includes = include_paths(raw_text)

        if path not in allowed_total_processed_refs and has_any_pattern(
            [r"\btotal_processed\b"], scanned_text
        ):
            failures.append(
                f"{path.relative_to(case_root)}: total_processed must stay owned by stats/reporter/main only."
            )

        if path not in allowed_stats_includes and any(
            include.endswith("stats.h") for include in includes
        ):
            failures.append(
                f"{path.relative_to(case_root)}: stats.h may only be included by reporter.cc, stats.cc, or app/main.cc."
            )

    protected_status = classify_relative_paths_against_baseline(
        case_root, baseline_root, PROTECTED_FILES
    )
    for relative_path in protected_status.missing_in_root:
        failures.append(f"{relative_path}: missing required starter file.")

    for relative_path in protected_status.missing_in_baseline:
        failures.append(f"{relative_path}: missing required baseline starter file.")

    for relative_path in protected_status.modified:
        failures.append(
            f"{relative_path}: must remain unchanged from the starter code."
        )

    return emit_check_result(passed=not failures, findings=failures)


if __name__ == "__main__":
    raise SystemExit(main())
