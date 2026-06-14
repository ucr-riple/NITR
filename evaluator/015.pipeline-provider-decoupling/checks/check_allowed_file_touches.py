#!/usr/bin/env python3

"""Limit touched paths to expected top-level case paths for case 015.

Rule:
  - Only allow file touches inside approved top-level directories/files.
  - Fail when a reported path is outside the boundary or missing.

Inputs:
  - Positional CLI arguments: candidate touched paths.
  - Repo root inferred from script location.

Output:
  - emit_check_result(passed=<bool>, findings=[...]).
"""

import argparse
from pathlib import Path

from evaluator.shared.check_output import emit_check_result
from evaluator.shared.path_checks import (
    find_missing_relative_paths,
    find_relative_paths_not_in_allowlist,
    find_paths_with_disallowed_top_level,
    repo_root_from_script,
)

ALLOWED_TOP_LEVEL_DIRS = {"app", "src"}
ALLOWED_ROOT_FILES = {"CMakeLists.txt", "TASK.md", "SPEC.md"}


def main() -> int:
    repo_root = repo_root_from_script(__file__)
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    if not args.paths:
        return emit_check_result(passed=True, findings=[])

    root_file_paths = [path for path in args.paths if "/" not in path]
    nested_paths = [path for path in args.paths if "/" in path]

    disallowed_paths = find_paths_with_disallowed_top_level(
        nested_paths, ALLOWED_TOP_LEVEL_DIRS
    )
    if disallowed_paths:
        return emit_check_result(
            passed=False,
            findings=[f"Forbidden modification target: {disallowed_paths[0]}"],
        )

    disallowed_root_files = find_relative_paths_not_in_allowlist(
        root_file_paths, ALLOWED_ROOT_FILES
    )
    if disallowed_root_files:
        return emit_check_result(
            passed=False,
            findings=[f"Forbidden modification target: {disallowed_root_files[0]}"],
        )

    missing_paths = find_missing_relative_paths(repo_root, args.paths)
    if missing_paths:
        return emit_check_result(
            passed=False,
            findings=[f"Path does not exist in repository: {missing_paths[0]}"],
        )
    return emit_check_result(passed=True, findings=[])


if __name__ == "__main__":
    raise SystemExit(main())
