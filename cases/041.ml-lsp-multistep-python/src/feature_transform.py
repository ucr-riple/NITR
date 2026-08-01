from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class FeatureTransform(ABC):
    @abstractmethod
    def transform(self, input_values: Sequence[float]) -> list[float]:
        """Return a transformed copy of one feature vector."""
