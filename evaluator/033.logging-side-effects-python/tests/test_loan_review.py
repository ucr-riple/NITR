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

from src.applicant import Applicant
from src.audit_logger import AuditLogger
from src.loan_policy import evaluate_applicant
from src.loan_review_service import review_applicants


class MemoryAuditLogger(AuditLogger):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def log(self, message: str) -> None:
        self.messages.append(message)


class LoanReviewTests(unittest.TestCase):
    def test_approves_eligible_applicant(self) -> None:
        decision = evaluate_applicant(Applicant("alice", 750, 90000, 0.20))

        self.assertTrue(decision.approved)
        self.assertEqual(decision.denial_reasons, [])

    def test_returns_ordered_denial_reasons(self) -> None:
        decision = evaluate_applicant(Applicant("carol", 680, 40000, 0.45))

        self.assertFalse(decision.approved)
        self.assertEqual(
            decision.denial_reasons,
            ["low_credit", "low_income", "high_debt"],
        )

    def test_accepts_rule_boundaries(self) -> None:
        decision = evaluate_applicant(Applicant("edge", 700, 50000, 0.40))

        self.assertTrue(decision.approved)
        self.assertEqual(decision.denial_reasons, [])

    def test_collects_approved_ids_and_audit_messages(self) -> None:
        applicants = [
            Applicant("alice", 750, 90000, 0.20),
            Applicant("bob", 650, 80000, 0.30),
            Applicant("carol", 710, 40000, 0.45),
        ]
        logger = MemoryAuditLogger()

        result = review_applicants(applicants, logger)

        self.assertEqual(result.approved_ids, ["alice"])
        self.assertEqual(
            logger.messages,
            [
                "alice approved",
                "bob denied: low_credit",
                "carol denied: low_income,high_debt",
            ],
        )

    def test_allows_a_missing_logger(self) -> None:
        applicants = [Applicant("alice", 750, 90000, 0.20)]

        result = review_applicants(applicants, None)

        self.assertEqual(result.approved_ids, ["alice"])


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
