from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FilterClause:
    field: str
    op: str
    value: str
