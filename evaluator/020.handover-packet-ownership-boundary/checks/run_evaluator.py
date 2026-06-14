#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CASE_NAME = Path(__file__).resolve().parents[1].name
ROOT = REPO_ROOT / "cases" / CASE_NAME
EVALUATOR_ROOT = REPO_ROOT / "evaluator" / CASE_NAME
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
    """Run structural sub-suite and emit a JSON summary."""
    structural_code, structural_payload = run_script(STRUCTURAL)
    findings: list[str] = []
    if structural_code != 0:
        findings.append("structural sub-suite failed")

    summary = {
        "case_id": "020-handover-packet-ownership-boundary",
        "passed": structural_code == 0,
        "findings": findings,
        "functional": {
            "status": "not executed in this script",
            "source": "case020_functional_tests via CTest",
        },
        "structural": structural_payload,
    }

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
