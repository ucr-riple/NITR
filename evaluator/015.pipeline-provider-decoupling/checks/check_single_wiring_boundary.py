#!/usr/bin/env python3
from __future__ import annotations

"""Ensure concrete provider wiring stays within designated boundary files.

Rule:
  - Concrete provider construction patterns are only permitted in a small allowed
    set of wiring files.
  - All other source files must remain free of those construction references.

Inputs:
  - `--case_root` (defaults to script's case root).
  - All `*.cc` / `*.h` under that case (except explicit whitelist).

Output:
  - emit_check_result(passed=<bool>, findings=[disallowed offender file paths]).
"""

import argparse
from pathlib import Path

from evaluator.shared.path_checks import (
    case_root_from_script,
    read_text,
    scan_files,
)
from evaluator.shared.source_analysis import has_any_pattern
from evaluator.shared.check_output import emit_check_result

ALLOWED_FILES = {
    "build_pipeline.cc",
    "main.cc",
    "static_policy_provider.cc",
    "file_policy_provider.cc",
}

FORBIDDEN_CREATION_PATTERNS = [
    r"\bStaticPolicyProvider\s+[A-Za-z_]",
    r"\bFilePolicyProvider\s+[A-Za-z_]",
    r"\bstd::make_unique\s*<\s*StaticPolicyProvider\s*>",
    r"\bstd::make_unique\s*<\s*FilePolicyProvider\s*>",
    r"\bstd::unique_ptr\s*<\s*StaticPolicyProvider\s*>",
    r"\bstd::unique_ptr\s*<\s*FilePolicyProvider\s*>",
    r"\bnew\s+StaticPolicyProvider\b",
    r"\bnew\s+FilePolicyProvider\b",
]


def main() -> int:
    """Ensure concrete provider construction stays inside the allowed wiring boundary."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    offenders: list[str] = []
    for path in scan_files(case_root, suffixes=(".cc", ".h")):
        text = read_text(path, missing_ok=False)
        if not has_any_pattern(FORBIDDEN_CREATION_PATTERNS, text):
            continue
        if path.name not in ALLOWED_FILES:
            offenders.append(str(path.relative_to(case_root)))

    return emit_check_result(passed=not offenders, findings=offenders)


if __name__ == "__main__":
    raise SystemExit(main())
