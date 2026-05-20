#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(cmd, cwd):
    print(f"[*] Running: {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Configure, build, and run a single NITR case."
    )
    parser.add_argument(
        "case",
        help="Case directory name under cases/, e.g. 002.refactor-and-reuse",
    )
    parser.add_argument(
        "--build-dir",
        default="build",
        help="Build directory relative to the repository root.",
    )
    parser.add_argument(
        "--with-evaluator",
        action="store_true",
        help="Enable evaluator targets and run registered tests/checks via CTest.",
    )
    parser.add_argument(
        "--configure-only",
        action="store_true",
        help="Only configure the selected case.",
    )
    args = parser.parse_args()

    case_dir = REPO_ROOT / "cases" / args.case
    if not case_dir.is_dir():
        parser.error(f"Unknown case: {args.case}")

    build_dir = REPO_ROOT / args.build_dir
    cmake_configure = [
        "cmake",
        "-S",
        str(REPO_ROOT),
        "-B",
        str(build_dir),
        "-DNITR_BUILD_ALL_CASES=OFF",
        f"-DNITR_CASE={args.case}",
        f"-DNITR_BUILD_EVALUATOR={'ON' if args.with_evaluator else 'OFF'}",
    ]
    run(cmake_configure, REPO_ROOT)

    if args.configure_only:
        return

    run(["cmake", "--build", str(build_dir)], REPO_ROOT)

    if args.with_evaluator:
        run(
            ["ctest", "--test-dir", str(build_dir), "--output-on-failure"],
            REPO_ROOT,
        )


if __name__ == "__main__":
    main()
