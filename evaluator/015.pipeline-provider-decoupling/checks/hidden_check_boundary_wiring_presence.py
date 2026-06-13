#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

from evaluator.shared.path_checks import case_root_from_script, read_text
from evaluator.shared.source_analysis import has_any_pattern
from evaluator.shared.check_output import emit_check_result

CREATION_PATTERNS = [
    r"\bstd::make_unique\s*<\s*StaticPolicyProvider\s*>",
    r"\bstd::make_unique\s*<\s*FilePolicyProvider\s*>",
    r"\bnew\s+StaticPolicyProvider\b",
    r"\bnew\s+FilePolicyProvider\b",
    r"\bStaticPolicyProvider\s+[A-Za-z_]",
    r"\bFilePolicyProvider\s+[A-Za-z_]",
]


def main() -> int:
    """Ensure the allowed boundary actually owns provider creation or selection."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    boundary_files = [case_root / "src/build_pipeline.cc", case_root / "app/main.cc"]
    boundary_has_wiring = False

    for path in boundary_files:
        text = read_text(path, missing_ok=False)
        if has_any_pattern(CREATION_PATTERNS, text):
            boundary_has_wiring = True
            break

    if not boundary_has_wiring:
        return emit_check_result(
            passed=False,
            findings=[
                "Expected provider creation/selection to appear in src/build_pipeline.cc or app/main.cc."
            ],
        )
    return emit_check_result(passed=True, findings=[])


if __name__ == "__main__":
    raise SystemExit(main())
