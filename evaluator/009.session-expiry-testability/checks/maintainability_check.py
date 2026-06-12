#!/usr/bin/env python3
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from evaluator.shared.check_utils import (
    case_root_from_script,
    evaluator_root_from_script,
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
def contains_any(patterns, text):
    """Return the subset of regex patterns that match the given text."""
    matches = []
    for pattern in patterns:
        if re.search(pattern, text):
            matches.append(pattern)
    return matches


failures = []

for path in scan_files(SRC_DIR, (".h", ".cc", ".cpp")):
    if path.name == "time_source.cc":
        continue
    text = path.read_text()
    forbidden = contains_any(FORBIDDEN_SRC_PATTERNS, text)
    suspicious = contains_any(SUSPICIOUS_API_PATTERNS, text)
    if forbidden:
        failures.append(
            f"forbidden time coupling in {path.relative_to(ROOT)}: {forbidden}"
        )
    if suspicious:
        failures.append(
            f"evaluation-only API smell in {path.relative_to(ROOT)}: {suspicious}"
        )

for path in scan_files(TEST_DIR, (".h", ".cc", ".cpp")):
    text = path.read_text()
    forbidden = contains_any(FORBIDDEN_TEST_PATTERNS, text)
    if forbidden:
        failures.append(
            f"sleep-based test detected in {path.relative_to(REPO_ROOT)}: {forbidden}"
        )

# Positive structural check: the time-injection seam must remain on the
# public SessionManager API. Without it, the seam can disappear silently and
# the only failure signal is a confusing test link error.
header_path = SRC_DIR / "session_manager.h"
if not header_path.exists():
    failures.append(
        "session_manager.h is missing from cases/009.session-expiry-testability/src/"
    )
else:
    header_text = header_path.read_text()
    seam_ctor = re.search(
        r"SessionManager\s*\([^)]*TimeSource[^)]*\)",
        header_text,
    )
    if seam_ctor is None:
        failures.append(
            "session_manager.h must keep a SessionManager constructor that "
            "accepts a TimeSource (the test seam)."
        )

if failures:
    for failure in failures:
        print(failure)
    sys.exit(1)

print("maintainability checks passed")
