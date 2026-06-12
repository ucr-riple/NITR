#!/usr/bin/env python3
from __future__ import annotations

from evaluator.shared.check_utils import case_root_from_script, has_any_pattern, read_text

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
    case_root = case_root_from_script(__file__)
    boundary_files = [case_root / "src/build_pipeline.cc", case_root / "app/main.cc"]
    boundary_has_wiring = False

    for path in boundary_files:
        text = read_text(path, missing_ok=False)
        if has_any_pattern(CREATION_PATTERNS, text):
            boundary_has_wiring = True
            break

    if not boundary_has_wiring:
        print(
            "Expected provider creation/selection to appear in src/build_pipeline.cc or app/main.cc."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
