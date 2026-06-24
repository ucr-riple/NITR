from __future__ import annotations

from src.snapshot import Snapshot


class SnapshotStore:
    def __init__(self) -> None:
        self._snapshots: dict[str, Snapshot] = {}
        self._active_version = ""
        self._has_active = False

    def register_snapshot(self, version: str, data: dict[str, str]) -> bool:
        if not version:
            return False

        # Baseline behavior: overwrite existing versions and retain caller-owned payload.
        self._snapshots[version] = Snapshot(version=version, data=data)
        if not self._has_active:
            self._active_version = version
            self._has_active = True
        return True

    def activate_snapshot(self, version: str) -> bool:
        if version not in self._snapshots:
            return False

        self._active_version = version
        self._has_active = True
        return True

    def reset_active_snapshot(self) -> None:
        self._has_active = False

    def get_active_snapshot(self) -> Snapshot | None:
        if not self._has_active:
            return None
        return self._snapshots.get(self._active_version)

    def get_active_version(self) -> str:
        if not self._has_active:
            return ""
        return self._active_version
