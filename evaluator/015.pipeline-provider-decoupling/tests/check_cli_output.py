#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run the CLI and compare its stdout line-for-line against the expected fixture."""
    if len(sys.argv) < 4:
        print(
            "Usage: check_cli_output.py <binary> <repo_root> <expected_file> [args...]",
            file=sys.stderr,
        )
        return 2

    binary = Path(sys.argv[1]).resolve()
    repo_root = Path(sys.argv[2]).resolve()
    expected_file = repo_root / sys.argv[3]
    extra_args = sys.argv[4:]

    expected = expected_file.read_text(encoding="utf-8").strip().splitlines()
    completed = subprocess.run(
        [str(binary), *extra_args],
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        print(f"CLI exited with status {completed.returncode}", file=sys.stderr)
        return completed.returncode

    actual = completed.stdout.strip().splitlines()
    if actual != expected:
        print("CLI output mismatch.", file=sys.stderr)
        print("Expected:", file=sys.stderr)
        for line in expected:
            print(line, file=sys.stderr)
        print("Actual:", file=sys.stderr)
        for line in actual:
            print(line, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
