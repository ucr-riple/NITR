#!/usr/bin/env python3
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CASE_NAME = pathlib.Path(__file__).resolve().parents[1].name
ROOT = REPO_ROOT / "cases" / CASE_NAME
EVALUATOR_ROOT = REPO_ROOT / "evaluator" / CASE_NAME
SRC_DIR = ROOT / "src"
TEST_DIR = EVALUATOR_ROOT / "tests"

FORBIDDEN_SRC_PATTERNS = [
    r"system_clock::now",
    r"steady_clock::now",
    r"high_resolution_clock::now",
    r"\bstd::time\s*\(",
    r"\bsleep_for\s*\(",
    r"\bsleep_until\s*\(",
]

FORBIDDEN_TEST_PATTERNS = [
    r"\bsleep_for\s*\(",
    r"\bsleep_until\s*\(",
    r"\bthis_thread::sleep_for\s*\(",
]

SUSPICIOUS_API_PATTERNS = [
    r"SetCurrentTimeForTest",
    r"ForceNowForTest",
    r"SetNowForTest",
    r"InjectNowForTest",
]


def scan_files(directory: pathlib.Path):
    """Collect source-like files under a directory for pattern scanning."""
    return [path for path in directory.rglob("*") if path.suffix in {".h", ".cc", ".cpp"}]


def contains_any(patterns, text):
    """Return the subset of regex patterns that match the given text."""
    matches = []
    for pattern in patterns:
        if re.search(pattern, text):
            matches.append(pattern)
    return matches


failures = []

for path in scan_files(SRC_DIR):
    if path.name == "time_source.cc":
        continue
    text = path.read_text()
    forbidden = contains_any(FORBIDDEN_SRC_PATTERNS, text)
    suspicious = contains_any(SUSPICIOUS_API_PATTERNS, text)
    if forbidden:
        failures.append(f"forbidden time coupling in {path.relative_to(ROOT)}: {forbidden}")
    if suspicious:
        failures.append(f"evaluation-only API smell in {path.relative_to(ROOT)}: {suspicious}")

for path in scan_files(TEST_DIR):
    text = path.read_text()
    forbidden = contains_any(FORBIDDEN_TEST_PATTERNS, text)
    if forbidden:
        failures.append(f"sleep-based test detected in {path.relative_to(ROOT)}: {forbidden}")

if failures:
    for failure in failures:
        print(failure)
    sys.exit(1)

print("maintainability checks passed")
