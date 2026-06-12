#!/usr/bin/env python3
# evaluator/checks/check.py

from __future__ import annotations

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Iterable, List, Tuple, Optional

from evaluator.shared.check_utils import (
    case_root_from_script,
    read_text as shared_read_text,
    repo_root_from_script,
    scan_files,
)


# ----------------------------
# Utilities
# ----------------------------


def die(msg: str, code: int = 1) -> None:
    """Print a fatal error message and exit the evaluator immediately."""
    print(msg, file=sys.stderr)
    sys.exit(code)


def case_root() -> Path:
    """Resolve the case directory that this evaluator should inspect."""
    return case_root_from_script(__file__)


def repo_root() -> Path:
    """Return the repository root inferred from this evaluator's location."""
    return repo_root_from_script(__file__)


def read_text(path: Path) -> str:
    """Read a text file or abort with a descriptive error."""
    try:
        return shared_read_text(
            path,
            encoding="utf-8",
            errors="replace",
            missing_ok=False,
        )
    except Exception as e:
        die(f"Failed to read {path}: {e}")


def list_files(base: Path, exts: Tuple[str, ...]) -> List[Path]:
    """Recursively collect files under a base directory that match the given suffixes."""
    return scan_files(base, exts)


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


def grep(pattern: re.Pattern, text: str) -> bool:
    """Return whether a compiled regex matches the provided text."""
    return bool(pattern.search(text))


def rel(p: Path, root: Path) -> str:
    """Render a path relative to the case root when possible."""
    try:
        return str(p.relative_to(root))
    except Exception:
        return str(p)


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
            die(f"Legacy file must NOT be modified: {lf.relative_to(root)}")


def check_no_legacy_includes(root: Path) -> None:
    """
    Enforce: no file outside legacy_monolith.* and evaluator/oracle_main.cc includes legacy_monolith.h
    """
    allowed = {
        "src/legacy_monolith.cc",
        "src/legacy_monolith.h",
        "evaluator/oracle_main.cc",
    }

    pat = re.compile(r'^\s*#\s*include\s*"legacy_monolith\.h"\s*$', re.MULTILINE)

    for p in list_files(root, (".cc", ".h")):
        rp = rel(p, root).replace("\\", "/")
        if rp in allowed:
            continue
        txt = read_text(p)
        if grep(pat, txt):
            die(f"Forbidden include of legacy_monolith.h in {rp}")


def check_no_legacy_symbol_references_in_source(root: Path) -> None:
    """
    Enforce: no source calls RunLegacyMonolith except legacy and oracle main.
    """
    allowed = {
        "src/legacy_monolith.cc",
        "src/legacy_monolith.h",
        "evaluator/oracle_main.cc",
    }
    pat = re.compile(r"\bRunLegacyMonolith\b")

    for p in list_files(root, (".cc", ".h")):
        rp = rel(p, root).replace("\\", "/")
        if rp in allowed:
            continue
        txt = read_text(p)
        if grep(pat, txt):
            die(f"Forbidden reference to RunLegacyMonolith in {rp}")


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

    for p in forbidden_files:
        if not p.exists():
            continue
        txt = read_text(p)
        if grep(forbid_io_include, txt):
            die(f"Forbidden include io_json.h in {rel(p, root)}")
        if grep(forbid_json_include, txt):
            die(f"Forbidden JSON usage/include in {rel(p, root)}")


def check_policy_dependency_restrictions(root: Path) -> None:
    """
    Enforce: src/policy.cc must not include normalize.h or estimator*.h
    """
    p = root / "src" / "policy.cc"
    if not p.exists():
        return
    txt = read_text(p)
    forbid = [
        re.compile(r'^\s*#\s*include\s*"normalize\.h"\s*$', re.MULTILINE),
        re.compile(r'^\s*#\s*include\s*"estimator.*\.h"\s*$', re.MULTILINE),
        re.compile(r'^\s*#\s*include\s*"estimator\.h"\s*$', re.MULTILINE),
    ]
    for pat in forbid:
        if grep(pat, txt):
            die(
                f"policy.cc must not include estimator/normalize headers: {rel(p, root)}"
            )


def find_binary(root: Path, name: str) -> Path:
    """
    Try common build output locations.
    """
    repo = repo_root()
    case_name = root.name
    candidates = [
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
    # Windows candidates
    candidates += [
        root / "build" / f"{name}.exe",
        root / "build" / "Release" / f"{name}.exe",
        root / "build" / "Debug" / f"{name}.exe",
        root / f"{name}.exe",
        repo / "build" / f"{name}.exe",
        repo / "build" / "Release" / f"{name}.exe",
        repo / "build" / "Debug" / f"{name}.exe",
        repo / "build" / "cases" / case_name / f"{name}.exe",
        repo / "build" / "cases" / case_name / "Release" / f"{name}.exe",
        repo / "build" / "cases" / case_name / "Debug" / f"{name}.exe",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    die(f"Cannot find binary '{name}' in common locations. Build it first.")


def maybe_find_binary(root: Path, name: str) -> Optional[Path]:
    """Find a build artifact if available, but tolerate it being absent."""
    try:
        return find_binary(root, name)
    except SystemExit:
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
    die(
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

    for pat in forbidden:
        if re.search(pat, sym):
            die(f"Binary isolation failed: '{pat}' found in {cv_bin}")


def run_named_check(name: str, fn, *args) -> None:
    """Run one check function and print a PASS banner if it succeeds."""
    fn(*args)
    print(f"PASS {name}")


def main() -> None:
    """Run source and binary isolation checks for the SRP case."""
    root = case_root()

    # Basic sanity
    if not (root / "src").exists():
        die("Missing src/ directory.")
    if not (root / "app").exists():
        die("Missing app/ directory.")
    # Static / source-level checks
    run_named_check("check_legacy_not_modified", check_legacy_not_modified, root)
    run_named_check("check_no_legacy_includes", check_no_legacy_includes, root)
    run_named_check(
        "check_no_legacy_symbol_references_in_source",
        check_no_legacy_symbol_references_in_source,
        root,
    )
    run_named_check("check_json_restrictions", check_json_restrictions, root)
    run_named_check(
        "check_policy_dependency_restrictions",
        check_policy_dependency_restrictions,
        root,
    )

    # Binary-level check (link isolation)
    cv_bin = maybe_find_binary(root, "cv_srp")
    if cv_bin is None:
        print("SKIP check_binary_symbol_isolation (cv_srp was not built)")
        print("OK")
        return
    run_named_check(
        "check_binary_symbol_isolation", check_binary_symbol_isolation, root
    )

    print("OK")


if __name__ == "__main__":
    main()
