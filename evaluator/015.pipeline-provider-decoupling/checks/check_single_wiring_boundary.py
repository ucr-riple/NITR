#!/usr/bin/env python3
from __future__ import annotations

from evaluator.shared.check_utils import (
    case_root_from_script,
    has_any_pattern,
    read_text,
    scan_files,
)

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
    case_root = case_root_from_script(__file__)
    offenders: list[str] = []
    for path in scan_files(case_root, suffixes=(".cc", ".h")):
        text = read_text(path, missing_ok=False)
        if not has_any_pattern(FORBIDDEN_CREATION_PATTERNS, text):
            continue
        if path.name not in ALLOWED_FILES:
            offenders.append(str(path.relative_to(case_root)))

    if offenders:
        print("Concrete provider creation escaped the allowed boundary:")
        for offender in offenders:
            print(f"- {offender}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
