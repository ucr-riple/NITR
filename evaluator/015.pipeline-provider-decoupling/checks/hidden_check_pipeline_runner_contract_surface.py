#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluator.shared.check_utils import case_root_from_script, read_text

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
    case_root = case_root_from_script(__file__)
    for path in [
        case_root / "src/pipeline_runner.h",
        case_root / "src/pipeline_runner.cc",
    ]:
        text = read_text(path, missing_ok=False)
        for pattern in FORBIDDEN:
            if re.search(pattern, text):
                print(
                    f"PipelineRunner contract leaks provider selection detail in {path}: {pattern}"
                )
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
