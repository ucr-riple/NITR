#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

FORBIDDEN_PATTERNS = [
    r"\bStaticPolicyProvider\b",
    r"\bFilePolicyProvider\b",
    r"\bBuildPolicyProvider\b",
    r"\bMakePolicyProvider\b",
    r"\bCreatePolicyProvider\b",
    r"\bProviderFactory\b",
    r"\bSelectPolicyProvider\b",
    r"\bpolicy_mode\b",
    r"\bpolicy_file_path\b",
    r"\bBuildPipeline\b",
    r"#include\s+\"build_pipeline\.h\"",
]


def main() -> int:
    """Reject provider selection or construction logic inside core pipeline files."""
    repo_root = Path(__file__).resolve().parents[3]
    case_root = repo_root / "cases" / Path(__file__).resolve().parents[1].name
    core_files = [case_root / "src/pipeline_runner.h", case_root / "src/pipeline_runner.cc"]
    for path in core_files:
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, text):
                print(f"Forbidden provider creation/selection hint in core file {path}: {pattern}")
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
