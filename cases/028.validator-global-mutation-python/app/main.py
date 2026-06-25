#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parents[1]
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

import src.stats as stats
from src.grader import Grader
from src.reporter import Reporter
from src.submission import Submission
from src.validator import Validator


def main() -> int:
    submissions = [
        Submission("alice", "Well-structured solution", False),
        Submission("bob", "", False),
        Submission("carol", "Late but complete", True),
        Submission("dana", "Concise answer", False),
    ]

    grader = Grader()
    validator = Validator()

    for submission in submissions:
        if not validator.validate(submission):
            continue

        stats.total_processed += 1
        print(f"{submission.student_id}: {grader.grade(submission)}")

    reporter = Reporter()
    print(reporter.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
