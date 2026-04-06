#!/usr/bin/env python3
import pathlib


def main() -> int:
    """Ensure pipeline_runner.cc routes execution planning through BuildExecutionPlan."""
    script_path = pathlib.Path(__file__).resolve()
    repo_root = script_path.parents[3]
    case_name = script_path.parents[1].name
    runner_path = repo_root / "cases" / case_name / "src" / "pipeline_runner.cc"
    if not runner_path.is_file():
        print(f"Could not find pipeline runner source: {runner_path}")
        return 1
    text = runner_path.read_text()
    if "BuildExecutionPlan(" not in text:
        print("pipeline_runner.cc does not appear to call BuildExecutionPlan(...)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
