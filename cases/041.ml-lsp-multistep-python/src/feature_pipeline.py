from __future__ import annotations

from collections.abc import Sequence

from src.feature_transform import FeatureTransform


class FeaturePipeline:
    def __init__(self, transform: FeatureTransform) -> None:
        self._transform = transform

    def run(self, features: Sequence[float]) -> list[float]:
        return self._transform.transform(features)
