#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

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
    repo_root = Path(__file__).resolve().parents[3]
    case_root = repo_root / "cases" / Path(__file__).resolve().parents[1].name
    boundary_files = [case_root / "src/build_pipeline.cc", case_root / "app/main.cc"]
    boundary_has_wiring = False

    for path in boundary_files:
        text = path.read_text(encoding="utf-8")
        if any(re.search(pattern, text) for pattern in CREATION_PATTERNS):
            boundary_has_wiring = True
            break

    if not boundary_has_wiring:
        print(
            "Expected provider creation/selection to appear in src/build_pipeline.cc or app/main.cc."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
