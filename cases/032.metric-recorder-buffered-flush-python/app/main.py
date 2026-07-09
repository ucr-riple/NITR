from __future__ import annotations

import sys

from src.console_metric_recorder import ConsoleMetricRecorder
from src.metric_collector import MetricCollector


def main() -> None:
    recorder = ConsoleMetricRecorder(sys.stdout)
    collector = MetricCollector(recorder)
    collector.collect([12.0, 18.0, 9.5, 22.0, 15.5])


if __name__ == "__main__":
    main()
