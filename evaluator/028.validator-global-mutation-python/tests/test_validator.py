#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib
import sys
import unittest
from pathlib import Path

ARG_PARSER = argparse.ArgumentParser()
ARG_PARSER.add_argument("--case_root", required=True)
ARGS = ARG_PARSER.parse_args()

CASE_ROOT = Path(ARGS.case_root).resolve()
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

import src.stats as stats
from src.grader import Grader
from src.reporter import Reporter
from src.submission import Submission
from src.validator import Validator


def reset_stats_module() -> None:
    importlib.reload(stats)


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_stats_module()

    def test_rejects_empty_submission_content(self) -> None:
        submission = Submission(student_id="alice", content="", is_late=False)
        validator = Validator()
        self.assertFalse(validator.validate(submission))

    def test_rejects_late_submission(self) -> None:
        submission = Submission(
            student_id="bob", content="complete answer", is_late=True
        )
        validator = Validator()
        self.assertFalse(validator.validate(submission))

    def test_accepts_valid_submission(self) -> None:
        submission = Submission(
            student_id="carol", content="complete answer", is_late=False
        )
        validator = Validator()
        self.assertTrue(validator.validate(submission))

    def test_empty_and_late_submission_is_rejected(self) -> None:
        submission = Submission(student_id="dana", content="", is_late=True)
        validator = Validator()
        self.assertFalse(validator.validate(submission))

    def test_validate_does_not_mutate_total_processed(self) -> None:
        validator = Validator()

        valid_submission = Submission(
            student_id="erin", content="complete answer", is_late=False
        )
        invalid_submission = Submission(student_id="frank", content="", is_late=False)

        stats.total_processed = 7
        _ = validator.validate(valid_submission)
        self.assertEqual(stats.total_processed, 7)

        stats.total_processed = 11
        _ = validator.validate(invalid_submission)
        self.assertEqual(stats.total_processed, 11)

    def test_caller_updates_total_processed_only_for_valid_submissions(self) -> None:
        submissions = [
            Submission("alice", "valid answer", False),
            Submission("bob", "", False),
            Submission("carol", "late answer", True),
            Submission("dana", "another valid answer", False),
        ]

        validator = Validator()
        grader = Grader()

        for submission in submissions:
            if not validator.validate(submission):
                continue

            stats.total_processed += 1
            _ = grader.grade(submission)

        self.assertEqual(stats.total_processed, 2)

    def test_reporter_summary_uses_global_processed_count(self) -> None:
        stats.total_processed = 3
        reporter = Reporter()
        self.assertEqual(reporter.summary(), "Processed 3 submissions")

    def test_grader_scores_by_content_length_capped_at_one_hundred(self) -> None:
        grader = Grader()

        short_submission = Submission(student_id="x", content="hello")
        self.assertEqual(grader.grade(short_submission), 5)

        long_submission = Submission(student_id="y", content=("x" * 120))
        self.assertEqual(grader.grade(long_submission), 100)

    def test_app_flow_processes_only_valid_submissions_and_summarizes(self) -> None:
        submissions = [
            Submission("alice", "Well-structured solution", False),
            Submission("bob", "", False),
            Submission("carol", "Late but complete", True),
            Submission("dana", "Concise answer", False),
        ]

        grader = Grader()
        validator = Validator()
        reporter = Reporter()
        output_lines: list[str] = []

        for submission in submissions:
            if not validator.validate(submission):
                continue
            stats.total_processed += 1
            output_lines.append(f"{submission.student_id}: {grader.grade(submission)}")

        output_lines.append(reporter.summary())

        def has_prefix(prefix: str) -> bool:
            return any(line.startswith(prefix) for line in output_lines)

        self.assertTrue(has_prefix("alice:"))
        self.assertTrue(has_prefix("dana:"))
        self.assertFalse(has_prefix("bob:"))
        self.assertFalse(has_prefix("carol:"))
        self.assertEqual(output_lines[-1], "Processed 2 submissions")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
