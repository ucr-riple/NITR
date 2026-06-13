#!/usr/bin/env python3
from __future__ import annotations

from evaluator.shared.path_checks import (
    case_root_from_script,
    read_text,
)
from evaluator.shared.source_analysis import find_matching_patterns

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
    violations = []
    for path in [
        case_root / "src/pipeline_runner.h",
        case_root / "src/pipeline_runner.cc",
    ]:
        text = read_text(path, missing_ok=False)
        for pattern in find_matching_patterns(FORBIDDEN, text):
            violations.append(
                f"PipelineRunner contract leaks provider selection detail in {path}: {pattern}"
            )
    for v in violations:
        print(v)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
