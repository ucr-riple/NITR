#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from evaluator.shared.check_utils import (
    find_missing_relative_paths,
    find_relative_paths_not_in_allowlist,
    find_paths_with_disallowed_top_level,
    repo_root_from_script,
)

ALLOWED_TOP_LEVEL_DIRS = {"app", "src"}
ALLOWED_ROOT_FILES = {"CMakeLists.txt", "TASK.md", "SPEC.md"}


def main() -> int:
    """Limit touched paths to the expected top-level case files and directories."""
    repo_root = repo_root_from_script(__file__)
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    if not args.paths:
        print("No file list provided; starter skeleton check passes by default.")
        return 0

    root_file_paths = [path for path in args.paths if "/" not in path]
    nested_paths = [path for path in args.paths if "/" in path]

    disallowed_paths = find_paths_with_disallowed_top_level(
        nested_paths, ALLOWED_TOP_LEVEL_DIRS
    )
    if disallowed_paths:
        print(f"Forbidden modification target: {disallowed_paths[0]}")
        return 1

    disallowed_root_files = find_relative_paths_not_in_allowlist(
        root_file_paths, ALLOWED_ROOT_FILES
    )
    if disallowed_root_files:
        print(f"Forbidden modification target: {disallowed_root_files[0]}")
        return 1

    missing_paths = find_missing_relative_paths(repo_root, args.paths)
    if missing_paths:
        print(f"Path does not exist in repository: {missing_paths[0]}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
