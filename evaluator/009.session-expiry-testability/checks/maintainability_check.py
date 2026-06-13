#!/usr/bin/env python3
import re

from evaluator.shared.check_utils import (
    case_root_from_script,
    evaluator_root_from_script,
    find_missing_paths,
    find_matching_patterns,
    has_any_pattern,
    scan_files,
)

ROOT = case_root_from_script(__file__)
EVALUATOR_ROOT = evaluator_root_from_script(__file__)
SRC_DIR = ROOT / "src"
TEST_DIR = EVALUATOR_ROOT / "tests"

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
    failures = []

    for path in scan_files(SRC_DIR, suffixes=(".h", ".cc", ".cpp")):
        if path.name == "time_source.cc":
            continue
        text = path.read_text()
        forbidden = find_matching_patterns(FORBIDDEN_SRC_PATTERNS, text)
        suspicious = find_matching_patterns(SUSPICIOUS_API_PATTERNS, text)
        if forbidden:
            failures.append(
                f"forbidden time coupling in {path.relative_to(ROOT)}: {forbidden}"
            )
        if suspicious:
            failures.append(
                f"evaluation-only API smell in {path.relative_to(ROOT)}: {suspicious}"
            )

    for path in scan_files(TEST_DIR, suffixes=(".h", ".cc", ".cpp")):
        text = path.read_text()
        forbidden = find_matching_patterns(FORBIDDEN_TEST_PATTERNS, text)
        if forbidden:
            failures.append(
                f"sleep-based test detected in {path.relative_to(EVALUATOR_ROOT)}: {forbidden}"
            )

    header_path = SRC_DIR / "session_manager.h"
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

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print("maintainability checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
