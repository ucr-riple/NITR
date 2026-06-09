#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

FORBIDDEN = [
    r"\bPolicyMode\b",
    r"\bpolicy_mode\b",
    r"\bpolicy_file_path\b",
    r"\bStaticPolicyProvider\b",
    r"\bFilePolicyProvider\b",
    r"\bBuildPipeline\b",
    r"\bBuildPolicyProvider\b",
    r"\bMakePolicyProvider\b",
    r"\bCreatePolicyProvider\b",
    r"\bProviderFactory\b",
    r"\bSelectPolicyProvider\b",
]


def main() -> int:
    """Ensure PipelineRunner does not expose provider-selection concerns in its contract."""
    repo_root = Path(__file__).resolve().parents[3]
    case_root = repo_root / "cases" / Path(__file__).resolve().parents[1].name
    for path in [
        case_root / "src/pipeline_runner.h",
        case_root / "src/pipeline_runner.cc",
    ]:
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN:
            if re.search(pattern, text):
                print(
                    f"PipelineRunner contract leaks provider selection detail in {path}: {pattern}"
                )
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
