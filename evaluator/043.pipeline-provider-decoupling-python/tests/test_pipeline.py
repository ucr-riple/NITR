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

from src.build_pipeline import build_pipeline
from src.models import Event, PipelineConfig, Policy
from src.pipeline_runner import PipelineRunner
from src.policy_provider import PolicyProvider

EVENTS = [
    Event("web", "login ok", 8),
    Event("mobile", "purchase confirmed", 12),
    Event("unknown", "manual review", 3),
]

BASELINE_OUTPUT = [
    "source=web;payload=LOGIN_OK;score=8",
    "source=mobile;payload=PURCHASE_CONFIRMED;score=12",
    "source=unknown;payload=MANUAL_REVIEW;score=3",
]


class SentinelProvider(PolicyProvider):
    def lookup(self, source_id: str) -> Policy:
        return Policy("sentinel", 7)


class PipelineTests(unittest.TestCase):
    def test_baseline(self) -> None:
        pipeline = build_pipeline(PipelineConfig())
        self.assertEqual(pipeline.runner.run(EVENTS), BASELINE_OUTPUT)

    def test_static(self) -> None:
        config = PipelineConfig(enable_policy_enrichment=True)
        output = build_pipeline(config).runner.run(EVENTS)

        self.assertEqual(
            output,
            [
                BASELINE_OUTPUT[0] + ";policy_tier=silver;retention_days=45",
                BASELINE_OUTPUT[1] + ";policy_tier=gold;retention_days=90",
                BASELINE_OUTPUT[2] + ";policy_tier=standard;retention_days=30",
            ],
        )

    def test_file_and_switching(self) -> None:
        policy_path = (
            Path(__file__).resolve().parents[1] / "data" / "policies.json"
        )
        config = PipelineConfig("file", str(policy_path), True)
        output = build_pipeline(config).runner.run(EVENTS)

        self.assertEqual(
            output,
            [
                BASELINE_OUTPUT[0] + ";policy_tier=gold;retention_days=120",
                BASELINE_OUTPUT[1] + ";policy_tier=silver;retention_days=60",
                BASELINE_OUTPUT[2] + ";policy_tier=standard;retention_days=30",
            ],
        )

    def test_unknown_mode_fallback(self) -> None:
        config = PipelineConfig("unknown", "", True)
        output = build_pipeline(config).runner.run([EVENTS[0]])

        self.assertEqual(
            output,
            [BASELINE_OUTPUT[0] + ";policy_tier=standard;retention_days=30"],
        )

    def test_runner_accepts_unknown_provider(self) -> None:
        runner = PipelineRunner(True, SentinelProvider())

        self.assertEqual(
            runner.run([EVENTS[0]]),
            [BASELINE_OUTPUT[0] + ";policy_tier=sentinel;retention_days=7"],
        )


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
