#!/usr/bin/env python3
"""Structural enforcement for case 004 (CV/SRP decomposition and dependency constraints).

Rules:
  - Prevent legacy monolith from being modified or referenced from unrelated files.
  - Restrict `nlohmann` JSON includes to permitted locations.
  - Enforce policy dependency boundary (no normalize/estimator includes in
    `src/policy.cc`).
  - Resolve and execute the expected case binary when present.

Inputs:
  - `--case_root` (defaults to script's case directory).

Inputs checked:
  - `src/legacy_monolith.*`
  - `evaluator/oracle_main.cc`
  - `src/io_json.*`
  - `src/estimator_e.cc`, `src/scoring.cc`, `src/policy.cc`, and related headers.

Output:
  - emit_check_result(passed=<bool>, findings=<messages list>) and
    optional execution reporting from the discovered test binary.
"""

import re
import subprocess
import argparse
from pathlib import Path
from typing import Iterable, List, Tuple, Optional

from evaluator.shared.path_checks import (
    case_root_from_script,
    find_missing_paths,
    read_text,
    repo_root_from_script,
    scan_files,
)
from evaluator.shared.source_analysis import find_matching_patterns, regex_matches
from evaluator.shared.check_output import emit_check_result


def run(cmd: List[str]) -> Tuple[int, str, str]:
    """Run a subprocess and return exit code, stdout, and stderr without raising."""
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return 1, "", f"Failed to run {cmd}: {e}"


def rel(p: Path, root: Path) -> str:
    """Render a path relative to the case root when possible."""
    try:
        return str(p.relative_to(root))
    except Exception:
        return str(p)


def existing_paths(paths: Iterable[Path]) -> list[Path]:
    """Return the subset of paths that currently exist on disk."""
    missing = set(find_missing_paths(paths))
    return [path for path in paths if path not in missing]


def scan_disallowed_patterns(
    root: Path,
    *,
    paths: Iterable[Path],
    allowed_relative_paths: set[str],
    patterns: Iterable[tuple[re.Pattern[str], str]],
) -> None:
    """Scan source files for forbidden patterns, skipping an allowlist."""
    for path in paths:
        relative_path = rel(path, root).replace("\\", "/")
        if relative_path in allowed_relative_paths:
            continue
        text = read_text(path, encoding="utf-8", errors="replace", missing_ok=False)
        for pattern, error_template in patterns:
            if regex_matches(pattern, text):
                raise RuntimeError(error_template.format(path=relative_path))


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


# ----------------------------
# Checks
# ----------------------------


def check_legacy_not_modified(root: Path) -> None:
    """
    Optional: If you're using git, fail if legacy_monolith.* was modified.
    Safe to skip if git not available.
    """
    legacy_files = [
        root / "src" / "legacy_monolith.cc",
        root / "src" / "legacy_monolith.h",
    ]
    if not any(p.exists() for p in legacy_files):
        return

    rc, out, err = run(["git", "status", "--porcelain"])
    if rc != 0:
        # no git env; skip
        return

    modified = set()
    for line in out.splitlines():
        # format: XY path
        if len(line) >= 4:
            modified.add(line[3:].strip())

    for lf in legacy_files:
        if lf.exists() and str(lf.relative_to(root)) in modified:
            raise RuntimeError(
                f"Legacy file must NOT be modified: {lf.relative_to(root)}"
            )


def check_no_legacy_includes(root: Path) -> None:
    """
    Enforce: no file outside legacy_monolith.* and evaluator/oracle_main.cc includes legacy_monolith.h
    """
    allowed = {
        "src/legacy_monolith.cc",
        "src/legacy_monolith.h",
        "evaluator/oracle_main.cc",
    }
    scan_disallowed_patterns(
        root,
        paths=scan_files(root, suffixes=(".cc", ".h")),
        allowed_relative_paths=allowed,
        patterns=[
            (
                re.compile(r'^\s*#\s*include\s*"legacy_monolith\.h"\s*$', re.MULTILINE),
                "Forbidden include of legacy_monolith.h in {path}",
            )
        ],
    )


def check_no_legacy_symbol_references_in_source(root: Path) -> None:
    """
    Enforce: no source calls RunLegacyMonolith except legacy and oracle main.
    """
    allowed = {
        "src/legacy_monolith.cc",
        "src/legacy_monolith.h",
        "evaluator/oracle_main.cc",
    }
    scan_disallowed_patterns(
        root,
        paths=scan_files(root, suffixes=(".cc", ".h")),
        allowed_relative_paths=allowed,
        patterns=[
            (
                re.compile(r"\bRunLegacyMonolith\b"),
                "Forbidden reference to RunLegacyMonolith in {path}",
            )
        ],
    )


def check_json_restrictions(root: Path) -> None:
    """
    Enforce: JSON only in src/io_json.*
    Specifically: forbid nlohmann/json includes in estimator/scoring/policy.
    """
    forbidden_files = [
        root / "src" / "estimator_e.cc",
        root / "src" / "scoring.cc",
        root / "src" / "policy.cc",
    ]
    # Also forbid including io_json.h in estimator/scoring/policy (SRP hard constraint)
    forbid_io_include = re.compile(r'^\s*#\s*include\s*"io_json\.h"\s*$', re.MULTILINE)
    forbid_json_include = re.compile(
        r'nlohmann\s*/\s*json|<\s*nlohmann/json\.hpp\s*>|"\s*nlohmann/json\.hpp\s*"'
    )

    for p in existing_paths(forbidden_files):
        txt = read_text(p, encoding="utf-8", errors="replace", missing_ok=False)
        if regex_matches(forbid_io_include, txt):
            raise RuntimeError(f"Forbidden include io_json.h in {rel(p, root)}")
        if regex_matches(forbid_json_include, txt):
            raise RuntimeError(f"Forbidden JSON usage/include in {rel(p, root)}")


def check_policy_dependency_restrictions(root: Path) -> None:
    """
    Enforce: src/policy.cc must not include normalize.h or estimator*.h
    """
    p = root / "src" / "policy.cc"
    if not existing_paths([p]):
        return
    txt = read_text(p, encoding="utf-8", errors="replace", missing_ok=False)
    forbid = [
        re.compile(r'^\s*#\s*include\s*"normalize\.h"\s*$', re.MULTILINE),
        re.compile(r'^\s*#\s*include\s*"estimator.*\.h"\s*$', re.MULTILINE),
        re.compile(r'^\s*#\s*include\s*"estimator\.h"\s*$', re.MULTILINE),
    ]
    for pat in forbid:
        if regex_matches(pat, txt):
            raise RuntimeError(
                f"policy.cc must not include estimator/normalize headers: {rel(p, root)}"
            )


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


def maybe_find_binary(root: Path, name: str) -> Optional[Path]:
    """Find a build artifact if available, but tolerate it being absent."""
    try:
        return find_binary(root, name)
    except RuntimeError:
        return None


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
    """Run source and binary isolation checks for the SRP case."""
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
    skipped_checks: list[str] = []

    try:
        missing_required_dirs = find_missing_paths([root / "src", root / "app"])
        if root / "src" in missing_required_dirs:
            raise RuntimeError("Missing src/ directory.")
        if root / "app" in missing_required_dirs:
            raise RuntimeError("Missing app/ directory.")

        check_legacy_not_modified(root)
        checks_run.append("check_legacy_not_modified")
        check_no_legacy_includes(root)
        checks_run.append("check_no_legacy_includes")
        check_no_legacy_symbol_references_in_source(root)
        checks_run.append("check_no_legacy_symbol_references_in_source")
        check_json_restrictions(root)
        checks_run.append("check_json_restrictions")
        check_policy_dependency_restrictions(root)
        checks_run.append("check_policy_dependency_restrictions")

        cv_bin = maybe_find_binary(root, "cv_srp")
        if cv_bin is None:
            skipped_checks.append("check_binary_symbol_isolation")
        else:
            check_binary_symbol_isolation(root)
            checks_run.append("check_binary_symbol_isolation")

        return emit_check_result(
            passed=True,
            findings=[],
            checks_run=checks_run,
            skipped_checks=skipped_checks,
        )
    except RuntimeError as exc:
        return emit_check_result(
            passed=False,
            findings=[str(exc)],
            checks_run=checks_run,
            skipped_checks=skipped_checks,
        )


if __name__ == "__main__":
    raise SystemExit(main())
