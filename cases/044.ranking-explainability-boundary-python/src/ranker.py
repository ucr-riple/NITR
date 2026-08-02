from __future__ import annotations

from collections.abc import Sequence

from src.models import Item, RankedItem


def category_adjustment(item: Item) -> int:
    return 15 if item.category_match else -8


def freshness_adjustment(item: Item) -> int:
    if item.freshness_days <= 3:
        return 12
    if item.freshness_days <= 14:
        return 4
    return -10


def popularity_adjustment(item: Item) -> int:
    return item.popularity // 5


def compute_score(item: Item) -> int:
    return (
        item.base_score
        + category_adjustment(item)
        + freshness_adjustment(item)
        + popularity_adjustment(item)
    )


class Ranker:
    def rank(self, items: Sequence[Item]) -> list[RankedItem]:
        ranked = [
            RankedItem(item, compute_score(item))
            for item in items
            if not item.is_blocked
        ]
        return sorted(
            ranked,
            key=lambda result: (
                -result.final_score,
                -result.item.base_score,
                result.item.id,
            ),
        )
