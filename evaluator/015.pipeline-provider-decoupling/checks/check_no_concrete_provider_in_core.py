#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

FORBIDDEN = [
    "static_policy_provider.h",
    "file_policy_provider.h",
    "StaticPolicyProvider",
    "FilePolicyProvider",
]


def main() -> int:
    """Reject concrete provider references from the pipeline runner core surface."""
    repo_root = Path(__file__).resolve().parents[3]
    case_root = repo_root / "cases" / Path(__file__).resolve().parents[1].name
    for path in [
        case_root / "src/pipeline_runner.h",
        case_root / "src/pipeline_runner.cc",
    ]:
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            if token in text:
                print(f"Forbidden concrete provider dependency in {path}: {token}")
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
