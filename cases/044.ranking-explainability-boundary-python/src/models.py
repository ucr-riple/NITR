from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    id: int
    name: str
    base_score: int
    category_match: bool
    freshness_days: int
    popularity: int
    is_blocked: bool


@dataclass(frozen=True)
class RankedItem:
    item: Item
    final_score: int
