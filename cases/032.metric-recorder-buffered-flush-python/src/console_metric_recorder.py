from __future__ import annotations

from typing import TextIO

from src.metric_recorder import Metric, MetricRecorder


class ConsoleMetricRecorder(MetricRecorder):
    def __init__(self, out: TextIO) -> None:
        self._out = out

    def record(self, metric: Metric) -> None:
        self._out.write(f"{metric.name}={metric.value}\n")
        self._out.flush()
