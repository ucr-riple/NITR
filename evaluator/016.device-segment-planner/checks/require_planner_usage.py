#!/usr/bin/env python3
import argparse
from pathlib import Path

from evaluator.shared.check_output import emit_check_result, fail_message
from evaluator.shared.path_checks import (
    case_root_from_script,
    read_text,
)


def main() -> int:
    """Ensure pipeline_runner.cc routes execution planning through BuildExecutionPlan."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()

    runner_path = case_root / "src" / "pipeline_runner.cc"
    if not runner_path.is_file():
        return fail_message(f"Could not find pipeline runner source: {runner_path}")
    text = read_text(runner_path, missing_ok=False)
    if "BuildExecutionPlan(" not in text:
        return fail_message(
            "pipeline_runner.cc does not appear to call BuildExecutionPlan(...)"
        )
    return emit_check_result(passed=True, findings=[])


if __name__ == "__main__":
    raise SystemExit(main())
