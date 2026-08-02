from __future__ import annotations

import math
from collections.abc import Sequence

from src.feature_transform import FeatureTransform


class L2NormalizeTransform(FeatureTransform):
    def transform(self, input_values: Sequence[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in input_values))
        return [value / norm for value in input_values]
