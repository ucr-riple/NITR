#!/usr/bin/env python3

import argparse
from pathlib import Path

from evaluator.shared.path_checks import case_root_from_script
from evaluator.shared.source_analysis import find_matching_paths
from evaluator.shared.check_output import emit_check_result


def main() -> int:
    """Enforce that active snapshot lifecycle state stays centralized in core ownership."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    failures: list[str] = []

    src_dir = case_root / "src"
    app_main = case_root / "app/main.cc"

    global_state_hits = find_matching_paths(
        r"\b(g_active|global_active|g_active_snapshot|g_active_version)\b", src_dir
    )
    if global_state_hits:
        failures.append(
            "Detected global mutable active-state variable naming pattern in src/."
        )

    tracker_files = {
        str(path)
        for path in find_matching_paths(
            r"active_version_|has_active_|current_active_|active_snapshot_",
            src_dir,
        )
        if path.suffix == ".h"
    }
    if len(tracker_files) > 1:
        failures.append(
            "Multiple headers contain writable active-state tracker fields."
        )

    # Check for value-type Snapshot members or data structure ownership (not just pointer caching)
    query_state_hits = find_matching_paths(
        r"(Snapshot\s+\w+_;|std::unordered_map<.*>\s+\w+_;)",
        root_dir / "src/query_service.h",
    )
    if query_state_hits:
        failures.append(
            "QueryService appears to own snapshot payload/state instead of depending on lifecycle owner."
        )

    lifecycle_control_hits = find_matching_paths(
        r"(if|for|while)\s*\(.*(RegisterSnapshot|ActivateSnapshot|ResetActiveSnapshot)",
        app_main,
    )
    if lifecycle_control_hits:
        failures.append(
            "Lifecycle control flow appears in app/main.cc; keep it in core src owner."
        )

    reset_mentions = {
        str(path)
        for path in find_matching_paths(r"ResetActiveSnapshot\s*\(", src_dir)
        if "snapshot_store" not in path.name
    }
    if reset_mentions:
        failures.append("ResetActiveSnapshot logic appears outside snapshot_store.*")

    return emit_check_result(passed=not failures, findings=failures)


if __name__ == "__main__":
    raise SystemExit(main())
