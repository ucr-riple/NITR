#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluator.shared.check_utils import case_root_from_script, read_text

FORBIDDEN = [
    "static_policy_provider.h",
    "file_policy_provider.h",
    "StaticPolicyProvider",
    "FilePolicyProvider",
]


def main() -> int:
    """Reject concrete provider references from the pipeline runner core surface."""
    case_root = case_root_from_script(__file__)
    for path in [
        case_root / "src/pipeline_runner.h",
        case_root / "src/pipeline_runner.cc",
    ]:
        text = read_text(path, missing_ok=False)
        for token in FORBIDDEN:
            if token in text:
                print(f"Forbidden concrete provider dependency in {path}: {token}")
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
