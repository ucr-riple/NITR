from __future__ import annotations

import json
import sys
from pathlib import Path

from src.map_snapshot import MapSnapshotService


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: map_snapshot <config.json>", file=sys.stderr)
        return 2
    try:
        config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except OSError:
        print("Failed to open config", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"Failed to parse JSON: {exc}", file=sys.stderr)
        return 2
    try:
        sys.stdout.write(MapSnapshotService().build_snapshot(config, sys.stdin.read()))
    except (TypeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
