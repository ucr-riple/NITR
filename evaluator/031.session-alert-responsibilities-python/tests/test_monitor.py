#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

ARG_PARSER = argparse.ArgumentParser()
ARG_PARSER.add_argument("--case_root", required=True)
ARGS = ARG_PARSER.parse_args()

CASE_ROOT = Path(ARGS.case_root).resolve()
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.monitor import Config, Event, EventKind, analyze


class SessionAlertTests(unittest.TestCase):
    def test_detects_range_alerts(self) -> None:
        config = Config(0.0, 50.0, 100.0)
        events = [
            Event("temp", EventKind.SAMPLE, 20.0),
            Event("temp", EventKind.SAMPLE, 60.0),
            Event("temp", EventKind.SAMPLE, -5.0),
        ]
        report = analyze(events, config)

        self.assertEqual(len(report.range_alerts), 2)
        self.assertEqual(report.range_alerts[0].channel, "temp")
        self.assertEqual(report.range_alerts[0].value, 60.0)
        self.assertEqual(report.range_alerts[1].channel, "temp")
        self.assertEqual(report.range_alerts[1].value, -5.0)
        self.assertEqual(report.drift_alerts, [])
        self.assertEqual(report.leak_alerts, [])

    def test_detects_drift_alerts_with_per_channel_baseline(self) -> None:
        config = Config(-1000.0, 1000.0, 5.0)
        events = [
            Event("a", EventKind.SAMPLE, 10.0),
            Event("a", EventKind.SAMPLE, 12.0),
            Event("a", EventKind.SAMPLE, 20.0),
            Event("b", EventKind.SAMPLE, 100.0),
            Event("b", EventKind.SAMPLE, 108.0),
            Event("a", EventKind.SAMPLE, 4.0),
        ]
        report = analyze(events, config)

        self.assertEqual(report.range_alerts, [])
        self.assertEqual(report.leak_alerts, [])
        self.assertEqual(len(report.drift_alerts), 3)
        self.assertEqual(report.drift_alerts[0].channel, "a")
        self.assertEqual(report.drift_alerts[0].value, 20.0)
        self.assertEqual(report.drift_alerts[0].baseline, 10.0)
        self.assertEqual(report.drift_alerts[1].channel, "b")
        self.assertEqual(report.drift_alerts[1].value, 108.0)
        self.assertEqual(report.drift_alerts[1].baseline, 100.0)
        self.assertEqual(report.drift_alerts[2].channel, "a")
        self.assertEqual(report.drift_alerts[2].value, 4.0)
        self.assertEqual(report.drift_alerts[2].baseline, 10.0)

    def test_detects_leaks_and_sorts_by_channel(self) -> None:
        config = Config(-1000.0, 1000.0, 1000.0)
        events = [
            Event("x", EventKind.ACQUIRE, 0.0),
            Event("y", EventKind.ACQUIRE, 0.0),
            Event("x", EventKind.RELEASE, 0.0),
            Event("z", EventKind.ACQUIRE, 0.0),
            Event("z", EventKind.ACQUIRE, 0.0),
            Event("z", EventKind.RELEASE, 0.0),
            Event("m", EventKind.SAMPLE, 1.0),
        ]
        report = analyze(events, config)

        self.assertEqual(len(report.leak_alerts), 2)
        self.assertEqual(report.leak_alerts[0].channel, "y")
        self.assertEqual(report.leak_alerts[1].channel, "z")

    def test_enforces_mixed_scenario_and_determinism(self) -> None:
        config = Config(0.0, 100.0, 10.0)
        events = [
            Event("p", EventKind.ACQUIRE, 0.0),
            Event("p", EventKind.SAMPLE, 50.0),
            Event("p", EventKind.SAMPLE, 150.0),
            Event("q", EventKind.SAMPLE, -3.0),
            Event("p", EventKind.RELEASE, 0.0),
            Event("q", EventKind.ACQUIRE, 0.0),
        ]
        report1 = analyze(events, config)
        report2 = analyze(events, config)

        self.assertEqual(len(report1.range_alerts), 2)
        self.assertEqual(report1.range_alerts[0].channel, "p")
        self.assertEqual(report1.range_alerts[0].value, 150.0)
        self.assertEqual(report1.range_alerts[1].channel, "q")
        self.assertEqual(report1.range_alerts[1].value, -3.0)

        self.assertEqual(len(report1.drift_alerts), 1)
        self.assertEqual(report1.drift_alerts[0].channel, "p")
        self.assertEqual(report1.drift_alerts[0].value, 150.0)
        self.assertEqual(report1.drift_alerts[0].baseline, 50.0)

        self.assertEqual(len(report1.leak_alerts), 1)
        self.assertEqual(report1.leak_alerts[0].channel, "q")

        self.assertEqual(report2, report1)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
