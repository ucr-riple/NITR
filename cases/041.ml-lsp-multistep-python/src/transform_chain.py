from __future__ import annotations

from collections.abc import Sequence

from src.feature_transform import FeatureTransform


class TransformChain(FeatureTransform):
    def __init__(self) -> None:
        self._steps: list[FeatureTransform] = []

    def add_step(self, transform: FeatureTransform) -> None:
        self._steps.append(transform)

    def transform(self, input_values: Sequence[float]) -> list[float]:
        return list(input_values)
