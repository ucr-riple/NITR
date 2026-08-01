from __future__ import annotations

from collections.abc import Sequence

from src.feature_transform import FeatureTransform


class ClampTransform(FeatureTransform):
    def transform(self, input_values: Sequence[float]) -> list[float]:
        return list(input_values)
