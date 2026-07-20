from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Report:
    title: str = ""
    columns: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
