#!/usr/bin/env python3
import pathlib
import re

from evaluator.shared.check_utils import find_matching_patterns, scan_files

FORBIDDEN_PATTERNS = [
    re.compile(r"==\s*4"),
    re.compile(r"==\s*6"),
    re.compile(r"==\s*3"),
    re.compile(r"==\s*5"),
    re.compile(r"legacy_gpu_through_step\(\)\.value\(\)\s*=="),
]

ALLOWLIST = {
    pathlib.Path(
        "evaluator/016.device-segment-planner/tests/execution_plan_legacy_test.cc"
    ),
    pathlib.Path(
        "evaluator/016.device-segment-planner/tests/execution_plan_updated_test.cc"
    ),
    pathlib.Path(
        "evaluator/016.device-segment-planner/tests/runner_respects_segmentation_test.cc"
    ),
}


def main() -> int:
    """Detect suspicious hardcoded step-index branching in production source files."""
    violations = []
    for path in scan_files(pathlib.Path("src"), suffixes=(".cc",)):
        if path in ALLOWLIST:
            continue
        text = path.read_text()
        for pattern in find_matching_patterns(FORBIDDEN_PATTERNS, text):
            violations.append(f"{path}: matched {pattern.pattern}")
    if violations:
        print("Suspicious step-index special-casing detected:")
        for violation in violations:
            print(violation)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
