from __future__ import annotations

from src.query_result import QueryResult, QueryStatus
from src.snapshot import Snapshot
from src.snapshot_store import SnapshotStore


class QueryService:
    def __init__(self, store: SnapshotStore) -> None:
        self._store = store
        self._bound_snapshot: Snapshot | None = None

    # Baseline wiring binds once and keeps a local alias.
    def bind_active_snapshot(self) -> None:
        self._bound_snapshot = self._store.get_active_snapshot()

    def lookup(self, key: str) -> QueryResult:
        if self._bound_snapshot is None:
            return QueryResult(
                status=QueryStatus.NO_ACTIVE_SNAPSHOT,
                value="",
                served_version="",
            )

        value = self._bound_snapshot.data.get(key)
        if value is None:
            return QueryResult(
                status=QueryStatus.NOT_FOUND,
                value="",
                served_version=self._bound_snapshot.version,
            )

        return QueryResult(
            status=QueryStatus.FOUND,
            value=value,
            served_version=self._bound_snapshot.version,
        )
