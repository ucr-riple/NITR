#!/usr/bin/env python3

"""Verify PipelineRunner contract has no provider-selection leakage (case 015).

Rule:
  - `pipeline_runner.{h,cc}` should not expose provider-selection or wiring details.
    Specifically, forbid policy-mode/provider-construction symbols in the runner contract.

Inputs:
  - `--case_root` (defaults to script-inferred case root)
  - Files:
      - `src/pipeline_runner.h`
      - `src/pipeline_runner.cc`

Output:
  - `{"passed": bool, "findings": [pattern-based violations]}` via emit_check_result.
"""

import argparse
from pathlib import Path

from evaluator.shared.module.path_checks import (
    case_root_from_script,
    read_text,
)
from evaluator.shared.module.source_analysis import find_matching_patterns
from evaluator.shared.check_output import emit_check_result

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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
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
    return emit_check_result(passed=not violations, findings=violations)


if __name__ == "__main__":
    raise SystemExit(main())
