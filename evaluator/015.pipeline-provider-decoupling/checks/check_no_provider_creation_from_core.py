#!/usr/bin/env python3
from __future__ import annotations

from evaluator.shared.path_checks import (
    case_root_from_script,
    read_text,
)
from evaluator.shared.source_analysis import find_matching_patterns

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
    case_root = case_root_from_script(__file__)
    core_files = [
        case_root / "src/pipeline_runner.h",
        case_root / "src/pipeline_runner.cc",
    ]
    violations = []
    for path in core_files:
        text = read_text(path, missing_ok=False)
        for pattern in find_matching_patterns(FORBIDDEN_PATTERNS, text):
            violations.append(
                f"Forbidden provider creation/selection hint in core file {path}: {pattern}"
            )
    for v in violations:
        print(v)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
