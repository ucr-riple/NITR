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

from src.report_renderer import render_inventory_report
from src.report_types import Item, ReportOptions, sample_items

EXPECTED_FULL = (
    "Inventory Report\n"
    "Items: 3\n"
    "- id=A-1, name=apple, qty=5\n"
    "- id=B-2, name=banana, qty=2\n"
    "- id=C-3, name=carrot, qty=7\n"
    "Summary\n"
    "Total quantity: 14\n"
)

EXPECTED_COMPACT = (
    "Inventory Report (compact)\n"
    "A-1:apple:5\n"
    "B-2:banana:2\n"
    "C-3:carrot:7\n"
    "Total quantity: 14\n"
)

EXPECTED_COMPACT_NO_SUMMARY = (
    "Inventory Report (compact)\nA-1:apple:5\nB-2:banana:2\nC-3:carrot:7\n"
)


class ConfigSprawlTests(unittest.TestCase):
    def test_full_mode_remains_unchanged(self) -> None:
        options = ReportOptions(include_summary=True)

        self.assertEqual(
            render_inventory_report(sample_items(), options), EXPECTED_FULL
        )

    def test_compact_mode_with_summary(self) -> None:
        options = ReportOptions(include_summary=True, compact_mode=True)

        self.assertEqual(
            render_inventory_report(sample_items(), options), EXPECTED_COMPACT
        )

    def test_compact_mode_without_summary(self) -> None:
        options = ReportOptions(include_summary=False, compact_mode=True)

        self.assertEqual(
            render_inventory_report(sample_items(), options),
            EXPECTED_COMPACT_NO_SUMMARY,
        )

    def test_compact_mode_defaults_to_false(self) -> None:
        self.assertFalse(ReportOptions().compact_mode)

    def test_renders_arbitrary_items(self) -> None:
        items = [Item("X", "xylophone", 4), Item("Y", "yam", 6)]
        options = ReportOptions(include_summary=True, compact_mode=True)

        self.assertEqual(
            render_inventory_report(items, options),
            "Inventory Report (compact)\nX:xylophone:4\nY:yam:6\nTotal quantity: 10\n",
        )


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
