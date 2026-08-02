from __future__ import annotations

from collections.abc import Sequence

from src.feature_transform import FeatureTransform


def transform_batch(
    transform: FeatureTransform, batch: Sequence[Sequence[float]]
) -> list[list[float]]:
    return []
