#!/usr/bin/env python3
# check.py — NITR structural checks for the add multi-type case
#
# Structural rules enforced:
#   1) app/main.cc must match the golden baseline (ignoring EOL style + trailing whitespace).
#   2) Forbid macro tricks: "#define add" anywhere under src/ or app/.
#   3) Maintainable implementation structure:
#        - A centralized, reusable core for add must exist (detected via generic-function patterns).
#        - Limit explicit per-type add overload DEFINITIONS to avoid copy-paste duplication.
#
# Notes:
# - Semantics are validated by unit tests/build; this script is structural only.
# - This is intentionally regex-based (fast, portable, and stable).

import argparse
import os
import re
from pathlib import Path

from evaluator.shared.check_output import emit_check_result
from evaluator.shared.path_checks import (
    normalize_text,
    read_text,
    scan_files,
)


MACRO_ADD_PATTERN = re.compile(r"^\s*#\s*define\s+add\b", re.MULTILINE)

# "Centralized reusable core" detection (generic function patterns).
# This intentionally does NOT require any specific file name or API shape.
GENERIC_ADD_PATTERNS = [
    # template<...> ... add(
    re.compile(
        r"\btemplate\s*<[^>]*>\s*(?:requires\s+[^\{;]+)?\s*"
        r"(?:constexpr\s+|inline\s+|static\s+)*"
        r"(?:auto|[\w:<>]+)\s+"
        r"(?:\w+\s*::\s*)?add\s*\(",
        re.MULTILINE,
    ),
    # abbreviated template: auto add(auto, auto)
    re.compile(
        r"\bauto\s+(?:\w+\s*::\s*)?add\s*\(\s*auto(?:\s+\w+)?\s*,\s*auto(?:\s+\w+)?\s*\)",
        re.MULTILINE,
    ),
]

# Count explicit overload *definitions* (copy-paste signal).
EXPLICIT_DEF_PATTERNS = [
    re.compile(
        r"\bint\s+(?:\w+\s*::\s*)?add\s*\(\s*int(?:\s+\w+)?\s*,\s*int(?:\s+\w+)?\s*\)\s*\{",
        re.MULTILINE,
    ),
    re.compile(
        r"\bdouble\s+(?:\w+\s*::\s*)?add\s*\(\s*double(?:\s+\w+)?\s*,\s*double(?:\s+\w+)?\s*\)\s*\{",
        re.MULTILINE,
    ),
    re.compile(
        r"\bfloat\s+(?:\w+\s*::\s*)?add\s*\(\s*float(?:\s+\w+)?\s*,\s*float(?:\s+\w+)?\s*\)\s*\{",
        re.MULTILINE,
    ),
    re.compile(
        r"\blong\s+long\s+(?:\w+\s*::\s*)?add\s*\(\s*long\s+long(?:\s+\w+)?\s*,\s*long\s+long(?:\s+\w+)?\s*\)\s*\{",
        re.MULTILINE,
    ),
]
def main() -> int:
    """Enforce frozen callsites and centralized add implementation structure."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--milestone", type=int, default=None)
    ap.add_argument("--case_root", type=str, default=".")
    ap.add_argument(
        "--baseline_case_root",
        type=str,
        required=True,
        help="Path to the original baseline case directory.",
    )
    ap.add_argument(
        "--freeze_from_milestone",
        type=int,
        default=1,
        help="Freeze app/main.cc starting from this milestone (default: 1).",
    )
    ap.add_argument(
        "--max_explicit_defs",
        type=int,
        default=1,
        help="Max allowed explicit add overload DEFINITIONS (default: 1).",
    )
    args = ap.parse_args()

    ms = args.milestone
    if ms is None:
        ms = int(os.environ.get("NITR_MILESTONE", "1"))
    if ms < 1:
        return emit_check_result(
            passed=False,
            findings=["ERR_BAD_MILESTONE"],
            details={"milestone": ms},
        )

    root = Path(args.case_root).resolve()
    baseline_root = Path(args.baseline_case_root).resolve()
    app_main = root / "app" / "main.cc"
    baseline_app_main = baseline_root / "app" / "main.cc"

    files = scan_files(
        root / "src",
        root / "app",
        suffixes=(".h", ".hpp", ".cc", ".cpp", ".cxx"),
    )
    if not files:
        return emit_check_result(
            passed=False,
            findings=["ERR_NO_CODE_FILES"],
            details={"searched": [str(root / "src"), str(root / "app")]},
        )

    # (1) Freeze app/main.cc
    if ms >= args.freeze_from_milestone:
        cur = read_text(app_main)
        baseline = read_text(baseline_app_main, missing_ok=False)
        if not cur:
            return emit_check_result(
                passed=False,
                findings=["ERR_MAIN_MISSING_OR_UNREADABLE"],
                details={"path": str(app_main)},
            )
        if normalize_text(cur) != normalize_text(baseline):
            return emit_check_result(
                passed=False,
                findings=["ERR_MAIN_MODIFIED"],
                details={
                    "path": str(app_main),
                    "baseline_path": str(baseline_app_main),
                    "milestone": ms,
                    "note": "app/main.cc must match golden baseline (ignoring EOL and trailing whitespace).",
                },
            )

    # (2) Anti-cheat: forbid macro rename of add
    macro_hits = []
    for f in files:
        txt = read_text(f)
        if txt and MACRO_ADD_PATTERN.search(txt):
            macro_hits.append(str(f))
    if macro_hits:
        return emit_check_result(
            passed=False,
            findings=["ERR_ADD_MACRO_FORBIDDEN"],
            details={"files": macro_hits},
        )

    # (3) Detect centralized reusable core (generic-function patterns)
    generic_hits = []
    for f in files:
        txt = read_text(f)
        if not txt:
            continue
        if any(p.search(txt) for p in GENERIC_ADD_PATTERNS):
            generic_hits.append(str(f))
    generic_present = len(generic_hits) > 0
    if not generic_present:
        return emit_check_result(
            passed=False,
            findings=["ERR_NON_MAINTAINABLE_STRUCTURE"],
            details={
                "note": "Implementation structure does not appear to centralize shared add behavior.",
                "hint": "Avoid duplicating per-type logic; keep shared behavior reusable/centralized.",
            },
        )

    # (4) Limit explicit overload definitions (copy-paste signal)
    explicit_def_files = []
    explicit_def_count = 0
    for f in files:
        txt = read_text(f)
        if not txt:
            continue
        for pat in EXPLICIT_DEF_PATTERNS:
            if pat.search(txt):
                explicit_def_count += 1
                explicit_def_files.append(str(f))
                break

    if explicit_def_count > args.max_explicit_defs:
        return emit_check_result(
            passed=False,
            findings=["ERR_DUPLICATED_IMPLEMENTATION"],
            details={
                "explicit_def_count": explicit_def_count,
                "max_allowed": args.max_explicit_defs,
                "files": sorted(set(explicit_def_files)),
                "note": "Too many explicit per-type add implementations; avoid copy-paste duplication.",
            },
        )

    return emit_check_result(
        passed=True,
        findings=[],
        milestone=ms,
        checks={
            "app_main_frozen": (ms < args.freeze_from_milestone)
            or (
                normalize_text(read_text(app_main))
                == normalize_text(read_text(baseline_app_main, missing_ok=False))
            ),
            "no_add_macro": (len(macro_hits) == 0),
            "structure_centralized": generic_present,
            "explicit_overload_def_count": explicit_def_count,
        },
        features={
            "central_core_files": generic_hits,
            "explicit_def_files": sorted(set(explicit_def_files)),
            "impl_style": ("mixed" if explicit_def_count > 0 else "centralized_only"),
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
