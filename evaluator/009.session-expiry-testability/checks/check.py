#!/usr/bin/env python3

"""Enforce session expiry testability constraints for case 009.

Rules:
  - Reject production time sources that couple logic to real time APIs.
  - Reject sleep-based waiting in evaluator unit tests.
  - Ensure `session_manager.h` keeps a constructor seam that accepts `TimeSource`.

Inputs:
  - `--case_root` (defaults to script-inferred case root)
  - `--evaluator_root` (defaults to script-inferred evaluator root)

Checks performed:
  - Scan `src/` for forbidden time APIs and evaluation-only time-control APIs.
  - Scan `evaluator/tests/` for sleep-related calls.
  - Verify `session_manager.h` exists and contains a `SessionManager` ctor that accepts `TimeSource`.

Output:
  - `{"passed": bool, "findings": [<rule_violation_strings>]}` via emit_check_result.
"""

import argparse
from pathlib import Path

from evaluator.shared.module.path_checks import (
    case_root_from_script,
    evaluator_root_from_script,
    find_missing_paths,
    scan_files,
)
from evaluator.shared.module.source_analysis import find_matching_patterns, has_any_pattern
from evaluator.shared.check_output import emit_check_result

FORBIDDEN_SRC_PATTERNS = [
    r"system_clock::now",
    r"steady_clock::now",
    r"high_resolution_clock::now",
    r"\bstd::time\s*\(",
    r"\bsleep_for\s*\(",
    r"\bsleep_until\s*\(",
    r"\bgettimeofday\s*\(",
    r"\bclock_gettime\s*\(",
    r"\bgmtime\s*\(",
    r"\blocaltime\s*\(",
    r"\bmktime\s*\(",
]

FORBIDDEN_TEST_PATTERNS = [
    r"\bsleep_for\s*\(",
    r"\bsleep_until\s*\(",
    r"\bthis_thread::sleep_for\s*\(",
    r"\busleep\s*\(",
    r"\bnanosleep\s*\(",
    r"(?<!_)\bsleep\s*\(",
]

SUSPICIOUS_API_PATTERNS = [
    r"SetCurrentTimeForTest",
    r"ForceNowForTest",
    r"SetNowForTest",
    r"InjectNowForTest",
]


def main() -> int:

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    parser.add_argument(
        "--evaluator_root",
        type=Path,
        default=evaluator_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    evaluator_root = args.evaluator_root.resolve()
    src_dir = case_root / "src"
    test_dir = evaluator_root / "tests"

    failures = []

    for path in scan_files(src_dir, suffixes=(".h", ".cc", ".cpp")):
        if path.name == "time_source.cc":
            continue
        text = path.read_text()
        forbidden = find_matching_patterns(FORBIDDEN_SRC_PATTERNS, text)
        suspicious = find_matching_patterns(SUSPICIOUS_API_PATTERNS, text)
        if forbidden:
            failures.append(
                f"forbidden time coupling in {path.relative_to(case_root)}: {forbidden}"
            )
        if suspicious:
            failures.append(
                f"evaluation-only API smell in {path.relative_to(case_root)}: {suspicious}"
            )

    for path in scan_files(test_dir, suffixes=(".h", ".cc", ".cpp")):
        text = path.read_text()
        forbidden = find_matching_patterns(FORBIDDEN_TEST_PATTERNS, text)
        if forbidden:
            failures.append(
                f"sleep-based test detected in {path.relative_to(evaluator_root)}: {forbidden}"
            )

    header_path = src_dir / "session_manager.h"
    if find_missing_paths([header_path]):
        failures.append(
            "session_manager.h is missing from cases/009.session-expiry-testability/src/"
        )
    else:
        header_text = header_path.read_text()
        if not has_any_pattern(
            [r"SessionManager\s*\([^)]*TimeSource[^)]*\)"], header_text
        ):
            failures.append(
                "session_manager.h must keep a SessionManager constructor that "
                "accepts a TimeSource (the test seam)."
            )

    return emit_check_result(passed=not failures, findings=failures)


if __name__ == "__main__":
    raise SystemExit(main())
