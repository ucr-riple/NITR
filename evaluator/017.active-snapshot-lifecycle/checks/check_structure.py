#!/usr/bin/env python3

from pathlib import Path
import re
import sys


CASE_REL = Path("cases/017.active-snapshot-lifecycle")


def search(pattern: str, *paths: Path):
    """Yield files whose contents match the given regex under the provided paths."""
    compiled = re.compile(pattern, re.MULTILINE)
    for path in paths:
        if path.is_dir():
            for file_path in sorted(path.rglob("*")):
                if file_path.suffix not in {".h", ".cc"}:
                    continue
                text = file_path.read_text(encoding="utf-8", errors="replace")
                if compiled.search(text):
                    yield file_path
        elif path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            if compiled.search(text):
                yield path


def main() -> int:
    """Enforce that active snapshot lifecycle state stays centralized in core ownership."""
    root_dir = Path.cwd() / CASE_REL
    failures: list[str] = []

    src_dir = root_dir / "src"
    app_main = root_dir / "app/main.cc"

    global_state_hits = list(
        search(r"\b(g_active|global_active|g_active_snapshot|g_active_version)\b", src_dir)
    )
    if global_state_hits:
        failures.append("Detected global mutable active-state variable naming pattern in src/.")

    tracker_files = {
        str(path)
        for path in search(
            r"active_version_|has_active_|current_active_|active_snapshot_",
            src_dir,
        )
        if path.suffix == ".h"
    }
    if len(tracker_files) > 1:
        failures.append("Multiple headers contain writable active-state tracker fields.")

    # Check for value-type Snapshot members or data structure ownership (not just pointer caching)
    query_state_hits = list(
        search(r"(Snapshot\s+\w+_;|std::unordered_map<.*>\s+\w+_;)", root_dir / "src/query_service.h")
    )
    if query_state_hits:
        failures.append(
            "QueryService appears to own snapshot payload/state instead of depending on lifecycle owner."
        )

    lifecycle_control_hits = list(
        search(r"(if|for|while)\s*\(.*(RegisterSnapshot|ActivateSnapshot|ResetActiveSnapshot)", app_main)
    )
    if lifecycle_control_hits:
        failures.append("Lifecycle control flow appears in app/main.cc; keep it in core src owner.")

    reset_mentions = {
        str(path)
        for path in search(r"ResetActiveSnapshot\s*\(", src_dir)
        if "snapshot_store" not in path.name
    }
    if reset_mentions:
        failures.append("ResetActiveSnapshot logic appears outside snapshot_store.*")

    for msg in failures:
        print(f"[STRUCTURE FAIL] {msg}")
    if failures:
        print(f"{len(failures)} structure check(s) failed.")
        return 1

    print("All structure checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
