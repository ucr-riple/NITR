from __future__ import annotations

from src.metric_recorder import Metric, MetricRecorder


class MetricCollector:
    def __init__(self, recorder: MetricRecorder) -> None:
        self._recorder = recorder

    def collect(self, samples: list[float]) -> None:
        if not samples:
            self._recorder.record(Metric("samples.count", 0.0))
            return

        sample_count = float(len(samples))
        sample_sum = sum(samples)
        max_value = max(samples)

        self._recorder.record(Metric("samples.count", sample_count))
        self._recorder.record(Metric("samples.mean", sample_sum / sample_count))
        self._recorder.record(Metric("samples.max", max_value))
