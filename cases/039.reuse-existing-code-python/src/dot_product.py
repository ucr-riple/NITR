from __future__ import annotations

from collections.abc import Sequence


def dot_product(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("dot_product: size mismatch")
    return sum(left * right for left, right in zip(a, b))
