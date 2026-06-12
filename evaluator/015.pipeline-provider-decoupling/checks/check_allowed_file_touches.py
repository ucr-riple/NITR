#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

from evaluator.shared.check_utils import repo_root_from_script

ALLOWED_TOP_LEVEL = {"app", "src", "CMakeLists.txt", "TASK.md", "SPEC.md"}


def main() -> int:
    """Limit touched paths to the expected top-level case files and directories."""
    repo_root = repo_root_from_script(__file__)
    if len(sys.argv) == 1:
        print("No file list provided; starter skeleton check passes by default.")
        return 0

    for raw_path in sys.argv[1:]:
        path = Path(raw_path)
        top = path.parts[0] if path.parts else ""
        if top not in ALLOWED_TOP_LEVEL:
            print(f"Forbidden modification target: {raw_path}")
            return 1
        if not (repo_root / raw_path).exists():
            print(f"Path does not exist in repository: {raw_path}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
