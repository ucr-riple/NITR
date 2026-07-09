from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Metric:
    name: str
    value: float


class MetricRecorder(ABC):
    @abstractmethod
    def record(self, metric: Metric) -> None:
        raise NotImplementedError
