#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from pathlib import Path

FORBIDDEN_TIME_PATTERNS = [
    r"\btime\.time\s*\(",
    r"\btime\.monotonic\s*\(",
    r"\btime\.perf_counter\s*\(",
    r"\btime\.monotonic_ns\s*\(",
    r"\btime\.perf_counter_ns\s*\(",
    r"\btime\.process_time_ns\s*\(",
    r"\btime_ns\s*\(",
    r"\bprocess_time\s*\(",
    r"\bdatetime\.(?:datetime\.)?now\s*\(",
    r"\bdatetime\.(?:datetime\.)?utcnow\s*\(",
    r"\bdatetime\.(?:datetime\.)?today\s*\(",
    r"\bdate\.today\s*\(",
    r"\btimezone\.now\s*\(",
    r"\basyncio\.sleep\s*\(",
    r"\btime\.sleep\s*\(",
]

FORBIDDEN_TEST_PATTERNS = [
    r"\btime\.sleep\s*\(",
    r"\basyncio\.sleep\s*\(",
    r"(?<![\w.])sleep\s*\(",
]

FORBIDDEN_TIME_SOURCE_PATTERNS = [
    r"\btime\.sleep\s*\(",
    r"\basyncio\.sleep\s*\(",
    r"\bos\.getenv\s*\(",
    r"\bos\.environ\b",
]

SUSPICIOUS_TEST_HOOK_PATTERNS = [
    r"SetCurrentTimeForTest",
    r"ForceNowForTest",
    r"SetNowForTest",
    r"InjectNowForTest",
    r"set_now_for_test",
    r"force_now_for_test",
    r"inject_now_for_test",
    r"set_current_time_for_test",
    r"freeze_time_for_test",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def scan_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root)
    src_dir = case_root / "src"
    evaluator_root = Path(__file__).resolve().parents[1]
    test_dir = evaluator_root / "tests"
    session_manager_path = src_dir / "session_manager.py"
    time_source_path = src_dir / "time_source.py"
    app_main = case_root / "app" / "main.py"

    required_paths = [
        session_manager_path,
        time_source_path,
        app_main,
    ]

    findings: list[str] = []
    for path in required_paths:
        if not path.is_file():
            findings.append(f"missing required path: {path.relative_to(case_root)}")

    for path in scan_python_files(src_dir):
        if path.name == "time_source.py":
            continue

        text = read_text(path)
        for pattern in FORBIDDEN_TIME_PATTERNS:
            if re.search(pattern, text):
                findings.append(
                    f"forbidden time coupling in {path.relative_to(case_root)}: session logic must not read wall-clock time directly."
                )
                break

        for pattern in SUSPICIOUS_TEST_HOOK_PATTERNS:
            if re.search(pattern, text):
                findings.append(
                    f"evaluation-only API smell in {path.relative_to(case_root)}: use the existing time seam instead of test-only time setters."
                )
                break

    for path in scan_python_files(test_dir):
        text = read_text(path)
        for pattern in FORBIDDEN_TEST_PATTERNS:
            if re.search(pattern, text):
                findings.append(
                    f"sleep-based test detected in {path.relative_to(evaluator_root)}: tests should advance manual time instead of waiting."
                )
                break

    if session_manager_path.is_file():
        session_manager_text = read_text(session_manager_path)

        if not re.search(
            r"def\s+__init__\s*\(\s*self\s*,[^)]*\btime_source\b",
            session_manager_text,
            re.DOTALL,
        ):
            findings.append(
                "session_manager.py must keep a SessionManager constructor seam that accepts time_source."
            )

    if time_source_path.is_file():
        time_source_text = read_text(time_source_path)
        if not re.search(r"\btime\.time\s*\(", time_source_text):
            findings.append(
                "time_source.py should remain the real-time adapter that reads system time."
            )
        if not re.search(r"class\s+TimeSource\b", time_source_text):
            findings.append(
                "time_source.py must define a TimeSource seam for deterministic time injection."
            )
        if not re.search(
            r"class\s+SystemTimeSource\s*\(\s*TimeSource\s*\)", time_source_text
        ):
            findings.append(
                "time_source.py must keep SystemTimeSource as the concrete real-time adapter."
            )
        if not re.search(r"def\s+now_seconds\s*\(", time_source_text):
            findings.append(
                "time_source.py must expose a now_seconds() time-reading entrypoint."
            )
        for pattern in FORBIDDEN_TIME_SOURCE_PATTERNS:
            if re.search(pattern, time_source_text):
                findings.append(
                    "time_source.py should remain a thin time adapter and must not add sleep or environment-driven behavior."
                )
                break
        for pattern in SUSPICIOUS_TEST_HOOK_PATTERNS:
            if re.search(pattern, time_source_text):
                findings.append(
                    "time_source.py should not expose test-only time-freezing or setter hooks."
                )
                break

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: structural checks succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
