from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToteRecord:
    tote_id: str
    package_count: int


class ShiftTracker:
    def __init__(self, shift_id: str) -> None:
        self._shift_id = shift_id
        self._completed_totes: list[ToteRecord] = []
        self._current_tote: ToteRecord | None = None

    def add_completed_tote(self, tote_id: str, package_count: int) -> None:
        self._completed_totes.append(ToteRecord(tote_id, package_count))

    def start_tote(self, tote_id: str) -> None:
        if self._current_tote is not None:
            raise RuntimeError("current tote already started")
        self._current_tote = ToteRecord(tote_id, 0)

    def scan_package_into_current_tote(self) -> None:
        self.scan_packages_into_current_tote(1)

    def scan_packages_into_current_tote(self, package_count: int) -> None:
        if self._current_tote is None:
            raise RuntimeError("no current tote")
        self._current_tote = ToteRecord(
            self._current_tote.tote_id,
            self._current_tote.package_count + package_count,
        )

    def close_current_tote(self) -> None:
        if self._current_tote is None:
            raise RuntimeError("no current tote")
        self._completed_totes.append(self._current_tote)
        self._current_tote = None

    @property
    def shift_id(self) -> str:
        return self._shift_id

    @property
    def completed_totes(self) -> tuple[ToteRecord, ...]:
        return tuple(self._completed_totes)

    @property
    def current_tote(self) -> ToteRecord | None:
        return self._current_tote
