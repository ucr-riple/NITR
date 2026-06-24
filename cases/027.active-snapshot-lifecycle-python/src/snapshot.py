from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Snapshot:
    version: str
    data: dict[str, str]
