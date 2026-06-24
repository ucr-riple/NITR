#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parents[1]
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.query_service import QueryService
from src.snapshot_store import SnapshotStore


def main() -> int:
    store = SnapshotStore()
    query = QueryService(store)

    store.register_snapshot("v1", {"color": "blue", "shape": "square"})
    store.activate_snapshot("v1")
    query.bind_active_snapshot()

    result = query.lookup("color")
    print(
        {
            "status": result.status.value,
            "value": result.value,
            "served_version": result.served_version,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
