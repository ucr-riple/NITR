#!/usr/bin/env python3

"""Reject provider creation/selection logic inside core pipeline files.

Rule:
  - Core runner files should not construct, select, or include provider factory
    machinery.

Inputs:
  - `--case_root` (defaults to script's case root).
  - Source files:
    - `src/pipeline_runner.h`
    - `src/pipeline_runner.cc`

Output:
  - emit_check_result(passed=<bool>, findings=[violation messages]).
"""

import argparse
from pathlib import Path

from evaluator.shared.path_checks import (
    case_root_from_script,
    read_text,
)
from evaluator.shared.source_analysis import find_matching_patterns
from evaluator.shared.check_output import emit_check_result

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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
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
    return emit_check_result(passed=not violations, findings=violations)


if __name__ == "__main__":
    raise SystemExit(main())
