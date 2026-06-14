#!/usr/bin/env python3

"""Detect hardcoded step-index branching in production code for case 016.

Rule:
  - Forbid suspicious `==` comparisons against legacy step literals that signal
    non-robust branching logic.

Inputs:
  - No explicit CLI args.
  - Scans `.cc` files under `src/`.
  - Ignores known test allowlisted files.

Output:
  - `{"passed": bool, "findings": [violations]}` via emit_check_result.
"""

from pathlib import Path
import re

from evaluator.shared.path_checks import scan_files
from evaluator.shared.source_analysis import find_matching_patterns
from evaluator.shared.check_output import emit_check_result

FORBIDDEN_PATTERNS = [
    re.compile(r"==\s*4"),
    re.compile(r"==\s*6"),
    re.compile(r"==\s*3"),
    re.compile(r"==\s*5"),
    re.compile(r"legacy_gpu_through_step\(\)\.value\(\)\s*=="),
]

ALLOWLIST = {
    Path("evaluator/016.device-segment-planner/tests/execution_plan_legacy_test.cc"),
    Path("evaluator/016.device-segment-planner/tests/execution_plan_updated_test.cc"),
    Path(
        "evaluator/016.device-segment-planner/tests/runner_respects_segmentation_test.cc"
    ),
}


def main() -> int:
    """Detect suspicious hardcoded step-index branching in production source files."""
    violations = []
    for path in scan_files(Path("src"), suffixes=(".cc",)):
        if path in ALLOWLIST:
            continue
        text = path.read_text()
        for pattern in find_matching_patterns(FORBIDDEN_PATTERNS, text):
            violations.append(f"{path}: matched {pattern.pattern}")
    return emit_check_result(passed=not violations, findings=violations)


if __name__ == "__main__":
    raise SystemExit(main())
