from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CASES_ROOT = REPO_ROOT / "cases"
EVALUATOR_ROOT = REPO_ROOT / "evaluator"


def read_text(path: Path) -> str:
    """Read a text file with forgiving UTF-8 decoding for repo metadata scans."""

    return path.read_text(encoding="utf-8", errors="replace")


def discover_case_slugs() -> list[str]:
    """List all case directory names under cases/."""

    return sorted(path.name for path in CASES_ROOT.iterdir() if path.is_dir())


def run_command(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run one subprocess and capture text output without raising on failure."""

    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def run_streaming_command(cmd: list[str], cwd: Path) -> int:
    """Run one subprocess, stream output to the terminal, and return its exit code."""

    print(f"[*] Running: {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)
    return completed.returncode
