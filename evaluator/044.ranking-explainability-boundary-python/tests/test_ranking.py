#!/usr/bin/env python3

from __future__ import annotations

import argparse
import contextlib
import importlib
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

from src.models import Item
from src.ranker import Ranker

ITEMS = [
    Item(10, "Top Match", 60, True, 1, 55, False),
    Item(11, "Stale Match", 67, True, 20, 40, False),
    Item(12, "Wrong Category", 75, False, 2, 35, False),
    Item(13, "Blocked Item", 99, True, 1, 90, True),
    Item(14, "Tie Winner", 70, True, 6, 25, False),
    Item(15, "Tie Loser", 68, True, 6, 35, False),
]


class RankingTests(unittest.TestCase):
    def inspection_module(self):
        return importlib.import_module("src.ranking_inspect")

    def test_baseline_order_and_scores(self) -> None:
        ranked = Ranker().rank(ITEMS)
        self.assertEqual([result.item.id for result in ranked], [10, 14, 15, 12, 11])
        self.assertEqual([result.final_score for result in ranked], [98, 94, 94, 86, 80])

    def test_reason_summaries(self) -> None:
        ranked = Ranker().rank(ITEMS)
        self.assertTrue(hasattr(ranked[0], "reason_summary"))
        self.assertEqual(ranked[0].reason_summary.final_score, 98)
        self.assertEqual(
            ranked[0].reason_summary.strongest_positive.name, "CATEGORY_MATCH"
        )
        self.assertEqual(ranked[0].reason_summary.strongest_negative.name, "NONE")
        self.assertEqual(
            ranked[3].reason_summary.strongest_negative.name,
            "CATEGORY_MISMATCH",
        )
        self.assertEqual(
            ranked[4].reason_summary.strongest_negative.name, "STALE_PENALTY"
        )

    def test_inspection_blocked_and_missing(self) -> None:
        module = self.inspection_module()
        blocked = module.inspect_candidate(ITEMS, 13)
        self.assertEqual(blocked.status.name, "BLOCKED")
        self.assertFalse(blocked.lost_on_tie_break)
        self.assertEqual(module.inspect_candidate(ITEMS, 404).status.name, "NOT_FOUND")

    def test_inspection_tie_break(self) -> None:
        result = self.inspection_module().inspect_candidate(ITEMS, 15)
        self.assertEqual(result.status.name, "RANKED")
        self.assertEqual(result.final_score, 94)
        self.assertTrue(result.lost_on_tie_break)
        self.assertEqual(result.tie_break_against_id, 14)

    def test_comparison(self) -> None:
        module = self.inspection_module()
        result = module.compare_candidates(ITEMS, 14, 15)
        self.assertEqual(result.status.name, "OK")
        self.assertEqual((result.winner_id, result.loser_id), (14, 15))
        self.assertTrue(result.decided_by_tie_break)
        self.assertEqual(result.decisive_reason.name, "BASE_SCORE_TIE_BREAK")
        self.assertEqual(
            module.compare_candidates(ITEMS, 10, 13).status.name,
            "NOT_APPLICABLE",
        )

    def test_no_logging_side_effects(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            Ranker().rank(ITEMS)
        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
