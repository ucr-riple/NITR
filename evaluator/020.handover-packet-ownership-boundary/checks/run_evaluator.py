#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CASE_NAME = Path(__file__).resolve().parents[1].name
ROOT = REPO_ROOT / "cases" / CASE_NAME
EVALUATOR_ROOT = REPO_ROOT / "evaluator" / CASE_NAME
FUNCTIONAL = EVALUATOR_ROOT / "tests" / "run_functional_tests.py"
STRUCTURAL = EVALUATOR_ROOT / "checks" / "check_structure.py"


def run_script(path: Path) -> tuple[int, dict]:
    """Run one child evaluator script and capture raw plus parsed output."""
    completed = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    payload = {
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.stdout.strip():
        try:
            payload["parsed"] = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload["parsed"] = None
    else:
        payload["parsed"] = None
    return completed.returncode, payload


def main() -> int:
    """Run functional and structural sub-suites and emit a combined JSON summary."""
    functional_code, functional_payload = run_script(FUNCTIONAL)
    structural_code, structural_payload = run_script(STRUCTURAL)

    summary = {
        "case_id": "020-handover-packet-ownership-boundary",
        "passed": functional_code == 0 and structural_code == 0,
        "functional": functional_payload,
        "structural": structural_payload,
    }

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
