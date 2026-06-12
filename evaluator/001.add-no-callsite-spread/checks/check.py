#!/usr/bin/env python3
# check.py — MaintainBench structural checks for the add multi-type case
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
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

from evaluator.shared.check_utils import normalize_text, read_text, scan_files


GOLDEN_APP_MAIN = """#include <iostream>

#include "add.h"

int main(int argc, char** argv) {
  std::cout << nitr::case001::add(3, 4) << "\\n";
  std::cout << nitr::case001::add(3.5, 4.5) << "\\n";
  std::cout << nitr::case001::add(100000000.0, 1.0) << "\\n";
  std::cout << nitr::case001::add(100000000, 100000000) << "\\n";
  return 0;
}
"""

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
def collect_code_files(root: Path) -> List[Path]:
    """Collect candidate source files under src/ and app/ for structural scanning."""
    files: List[Path] = []
    for dname in ["src", "app"]:
        d = root / dname
        if not d.exists():
            continue
        files.extend(scan_files(d, (".h", ".hpp", ".cc", ".cpp", ".cxx")))
    return sorted(set(files), key=lambda x: str(x))


def fail(msg: str, details: Dict) -> None:
    """Emit a structured failure payload and terminate the evaluator."""
    print(
        json.dumps(
            {"ok": False, "error": msg, "details": details},
            indent=2,
            ensure_ascii=False,
        )
    )
    sys.exit(1)


def main() -> int:
    """Enforce frozen callsites and centralized add implementation structure."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--milestone", type=int, default=None)
    ap.add_argument("--case_root", type=str, default=".")
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
        fail("ERR_BAD_MILESTONE", {"milestone": ms})

    root = Path(args.case_root).resolve()
    app_main = root / "app" / "main.cc"

    files = collect_code_files(root)
    if not files:
        fail("ERR_NO_CODE_FILES", {"searched": [str(root / "src"), str(root / "app")]})

    # (1) Freeze app/main.cc
    if ms >= args.freeze_from_milestone:
        cur = read_text(app_main)
        if not cur:
            fail("ERR_MAIN_MISSING_OR_UNREADABLE", {"path": str(app_main)})
        if normalize_text(cur) != normalize_text(GOLDEN_APP_MAIN):
            fail(
                "ERR_MAIN_MODIFIED",
                {
                    "path": str(app_main),
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
        fail("ERR_ADD_MACRO_FORBIDDEN", {"files": macro_hits})

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
        fail(
            "ERR_NON_MAINTAINABLE_STRUCTURE",
            {
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
        fail(
            "ERR_DUPLICATED_IMPLEMENTATION",
            {
                "explicit_def_count": explicit_def_count,
                "max_allowed": args.max_explicit_defs,
                "files": sorted(set(explicit_def_files)),
                "note": "Too many explicit per-type add implementations; avoid copy-paste duplication.",
            },
        )

    out = {
        "ok": True,
        "milestone": ms,
        "checks": {
            "app_main_frozen": (ms < args.freeze_from_milestone)
            or (normalize_text(read_text(app_main)) == normalize_text(GOLDEN_APP_MAIN)),
            "no_add_macro": (len(macro_hits) == 0),
            "structure_centralized": generic_present,
            "explicit_overload_def_count": explicit_def_count,
        },
        "features": {
            "central_core_files": generic_hits,
            "explicit_def_files": sorted(set(explicit_def_files)),
            "impl_style": ("mixed" if explicit_def_count > 0 else "centralized_only"),
        },
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
