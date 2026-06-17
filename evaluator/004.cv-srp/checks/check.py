#!/usr/bin/env python3

"""Binary symbol isolation check for case 004.

This script intentionally keeps only the binary-level isolation assertion that
current generic modules do not express well. Source-level include/dependency
checks are handled by pipeline modules.

Inputs:
  - `--case_root` (defaults to script's case directory).

Inputs checked:
  - built `cv_srp` binary

Output:
  - emit_check_result(passed=<bool>, findings=<messages list>) and
    optional execution reporting from the discovered test binary.
"""

import re
import subprocess
import argparse
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from evaluator.shared.module.path_checks import case_root_from_script, repo_root_from_script
from evaluator.shared.module.source_analysis import find_matching_patterns
from evaluator.shared.check_output import RunResult, emit_check_result


def run(cmd: List[str]) -> Tuple[int, str, str]:
    """Run a subprocess and return exit code, stdout, and stderr without raising."""
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return RunResult.COMMAND_NOT_FOUND, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return RunResult.FAILED, "", f"Failed to run {cmd}: {e}"


def binary_candidates(root: Path, name: str) -> list[Path]:
    """Enumerate common build-output paths for a named binary."""
    repo = repo_root_from_script(__file__)
    case_name = root.name
    base_candidates = [
        root / "build" / name,
        root / "build" / "Release" / name,
        root / "build" / "Debug" / name,
        root / name,
        repo / "build" / name,
        repo / "build" / "Release" / name,
        repo / "build" / "Debug" / name,
        repo / "build" / "cases" / case_name / name,
        repo / "build" / "cases" / case_name / "Release" / name,
        repo / "build" / "cases" / case_name / "Debug" / name,
    ]
    windows_candidates = [
        path.parent / f"{path.name}.exe" if path.suffix != ".exe" else path
        for path in base_candidates
    ]
    return base_candidates + windows_candidates

def find_binary(root: Path, name: str) -> Path:
    """
    Try common build output locations.
    """
    for c in binary_candidates(root, name):
        if c.exists() and c.is_file():
            return c
    raise RuntimeError(
        f"Cannot find binary '{name}' in common locations. Build it first."
    )


def symbols_via_nm(bin_path: Path) -> Optional[str]:
    """Try extracting symbols with nm."""
    rc, out, err = run(["nm", "-a", str(bin_path)])
    if rc == 0 and out.strip():
        return out
    return None


def symbols_via_objdump(bin_path: Path) -> Optional[str]:
    """Try extracting symbols with objdump."""
    # Linux: objdump -t; mac: gobjdump may exist but not guaranteed
    rc, out, err = run(["objdump", "-t", str(bin_path)])
    if rc == 0 and out.strip():
        return out
    return None


def symbols_via_dumpbin(bin_path: Path) -> Optional[str]:
    """Try extracting symbols with dumpbin on Windows toolchains."""
    # Windows Visual Studio toolchain
    rc, out, err = run(["dumpbin", "/SYMBOLS", str(bin_path)])
    if rc == 0 and out.strip():
        return out
    return None


def extract_symbols(bin_path: Path) -> str:
    """
    Best-effort cross-platform symbol dump.
    """
    for fn in [symbols_via_nm, symbols_via_objdump, symbols_via_dumpbin]:
        s = fn(bin_path)
        if s is not None:
            return s
    raise RuntimeError(
        "No symbol tool available (nm/objdump/dumpbin). Cannot enforce symbol isolation."
    )


def check_binary_symbol_isolation(root: Path) -> None:
    """
    Enforce: cv_srp binary must not contain legacy/oracle symbols.
    """
    cv_bin = find_binary(root, "cv_srp")
    sym = extract_symbols(cv_bin)

    # Things that MUST NOT appear in cv_srp
    forbidden = [
        r"\bRunLegacyMonolith\b",
        r"\bEstimateE_RansacMath\b",
        r"\bEightPointE\b",
        r"\blegacy_monolith\b",
    ]

    for pat in find_matching_patterns(forbidden, sym):
        raise RuntimeError(f"Binary isolation failed: '{pat}' found in {cv_bin}")


def main() -> int:
    """Run binary isolation checks for the SRP case."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
        help="Path to the case root (defaults to the case inferred from this script).",
    )
    args = parser.parse_args()

    root = args.case_root.resolve()
    checks_run: list[str] = []

    try:
        check_binary_symbol_isolation(root)
        checks_run.append("check_binary_symbol_isolation")

        return emit_check_result(
            passed=True,
            findings=[],
            checks_run=checks_run,
        )
    except RuntimeError as exc:
        return emit_check_result(
            passed=False,
            findings=[str(exc)],
            checks_run=checks_run,
        )


if __name__ == "__main__":
    raise SystemExit(main())
