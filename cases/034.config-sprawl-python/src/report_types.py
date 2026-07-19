from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    quantity: int = 0


@dataclass(frozen=True)
class ReportOptions:
    include_summary: bool = True


def sample_items() -> list[Item]:
    return [
        Item("A-1", "apple", 5),
        Item("B-2", "banana", 2),
        Item("C-3", "carrot", 7),
    ]
