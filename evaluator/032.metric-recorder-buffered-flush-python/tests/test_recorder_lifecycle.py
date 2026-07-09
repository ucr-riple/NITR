#!/usr/bin/env python3

from __future__ import annotations

import argparse
import io
import sys
import unittest
from pathlib import Path

ARG_PARSER = argparse.ArgumentParser()
ARG_PARSER.add_argument("--case_root", required=True)
ARGS = ARG_PARSER.parse_args()

CASE_ROOT = Path(ARGS.case_root).resolve()
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.console_metric_recorder import ConsoleMetricRecorder
from src.metric_collector import MetricCollector
from src.metric_recorder import Metric, MetricRecorder

try:
    from src.buffered_metric_recorder import BufferedMetricRecorder
except ModuleNotFoundError:
    BufferedMetricRecorder = None


class RecorderLifecycleTests(unittest.TestCase):
    def test_console_recorder_writes_each_metric_immediately(self) -> None:
        out = io.StringIO()
        recorder = ConsoleMetricRecorder(out)

        recorder.record(Metric("requests", 1.0))
        self.assertNotEqual(out.getvalue(), "")

        recorder.record(Metric("errors", 2.0))
        output = out.getvalue()
        self.assertIn("requests", output)
        self.assertIn("errors", output)

    def test_buffered_recorder_class_exists(self) -> None:
        self.assertIsNotNone(
            BufferedMetricRecorder,
            msg="src.buffered_metric_recorder.BufferedMetricRecorder must exist.",
        )

    def test_buffered_recorder_defers_visibility_before_capacity_or_flush(self) -> None:
        self.assertIsNotNone(BufferedMetricRecorder)
        out = io.StringIO()
        recorder = BufferedMetricRecorder(out, capacity=8)

        recorder.record(Metric("a", 1.0))
        recorder.record(Metric("b", 2.0))
        recorder.record(Metric("c", 3.0))

        self.assertEqual(out.getvalue(), "")

    def test_buffered_recorder_flushes_when_capacity_is_reached(self) -> None:
        self.assertIsNotNone(BufferedMetricRecorder)
        out = io.StringIO()
        recorder = BufferedMetricRecorder(out, capacity=3)

        recorder.record(Metric("a", 1.0))
        recorder.record(Metric("b", 2.0))
        self.assertEqual(out.getvalue(), "")

        recorder.record(Metric("c", 3.0))
        output = out.getvalue()
        self.assertNotEqual(output, "")
        self.assertIn("a", output)
        self.assertIn("b", output)
        self.assertIn("c", output)

    def test_explicit_flush_makes_queued_metrics_visible(self) -> None:
        self.assertIsNotNone(BufferedMetricRecorder)
        out = io.StringIO()
        recorder = BufferedMetricRecorder(out, capacity=100)

        base: MetricRecorder = recorder
        base.record(Metric("queued1", 10.0))
        base.record(Metric("queued2", 20.0))
        self.assertEqual(out.getvalue(), "")

        base.flush()

        output = out.getvalue()
        self.assertIn("queued1", output)
        self.assertIn("queued2", output)

    def test_checkpoint_flushes_underlying_buffered_recorder(self) -> None:
        self.assertIsNotNone(BufferedMetricRecorder)
        out = io.StringIO()
        recorder = BufferedMetricRecorder(out, capacity=100)

        abstract_ref: MetricRecorder = recorder
        collector = MetricCollector(abstract_ref)

        collector.collect([1.0, 2.0, 3.0])
        self.assertEqual(out.getvalue(), "")

        collector.checkpoint()

        output = out.getvalue()
        self.assertIn("samples.count", output)
        self.assertIn("samples.mean", output)
        self.assertIn("samples.max", output)

    def test_checkpoint_is_harmless_for_immediate_recorder(self) -> None:
        out = io.StringIO()
        recorder = ConsoleMetricRecorder(out)
        collector = MetricCollector(recorder)

        collector.collect([4.0, 5.0])
        before_checkpoint = out.getvalue()
        self.assertNotEqual(before_checkpoint, "")

        collector.checkpoint()

        after_checkpoint = out.getvalue()
        self.assertGreaterEqual(len(after_checkpoint), len(before_checkpoint))
        self.assertIn("samples.count", after_checkpoint)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
