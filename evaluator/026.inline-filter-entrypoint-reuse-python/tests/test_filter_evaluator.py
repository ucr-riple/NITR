#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import sys
import unittest
from pathlib import Path

ARG_PARSER = argparse.ArgumentParser()
ARG_PARSER.add_argument("--case_root", required=True)
ARG_PARSER.add_argument("--data_dir", required=True)
ARGS = ARG_PARSER.parse_args()

CASE_ROOT = Path(ARGS.case_root).resolve()
DATA_DIR = Path(ARGS.data_dir).resolve()

if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.filter_clause import FilterClause
from src.filter_parser import parse_filter_clause, parse_inline_filter
from src.filter_rule import FilterErrorCode, FilterRule, FilterValueKind


def read_csv_rows(file_name: str) -> list[dict[str, str]]:
    with (DATA_DIR / file_name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_error_code_name(text: str) -> FilterErrorCode:
    return FilterErrorCode(text)


def expect_rule(
    test_case: unittest.TestCase,
    rule: FilterRule,
    expected_field: str,
    expected_op: str,
    expected_kind: str,
    expected_value: str,
) -> None:
    test_case.assertEqual(rule.field.value, expected_field)
    test_case.assertEqual(rule.op.value, expected_op)
    if expected_kind == "integer":
        test_case.assertEqual(rule.value.kind, FilterValueKind.INTEGER)
        test_case.assertEqual(str(rule.value.number), expected_value)
    else:
        test_case.assertEqual(rule.value.kind, FilterValueKind.TEXT)
        test_case.assertEqual(rule.value.text, expected_value)


class FilterEvaluatorTests(unittest.TestCase):
    def test_structured_valid_cases(self) -> None:
        for row in read_csv_rows("structured_valid.csv"):
            result = parse_filter_clause(
                FilterClause(field=row["field"], op=row["op"], value=row["value"])
            )
            self.assertTrue(result.ok, msg=f"structured parse should succeed for {row}")
            if result.ok:
                expect_rule(
                    self,
                    result.rule,
                    row["expected_field"],
                    row["expected_op"],
                    row["value_kind"],
                    row["expected_value"],
                )

    def test_inline_valid_cases(self) -> None:
        for row in read_csv_rows("inline_valid.csv"):
            result = parse_inline_filter(row["inline"])
            self.assertTrue(
                result.ok, msg=f"inline parse should succeed for {row['inline']}"
            )
            if result.ok:
                expect_rule(
                    self,
                    result.rule,
                    row["expected_field"],
                    row["expected_op"],
                    row["value_kind"],
                    row["expected_value"],
                )

    def test_inline_invalid_cases(self) -> None:
        for row in read_csv_rows("inline_invalid.csv"):
            result = parse_inline_filter(row["inline"])
            self.assertFalse(
                result.ok, msg=f"inline parse should fail for {row['inline']}"
            )
            if not result.ok:
                self.assertEqual(
                    result.error.code,
                    parse_error_code_name(row["error_code"]),
                    msg=f"unexpected error code for {row['inline']}",
                )

    def test_parity_between_structured_and_inline_parsing(self) -> None:
        for row in read_csv_rows("parity_cases.csv"):
            structured = parse_filter_clause(
                FilterClause(field=row["field"], op=row["op"], value=row["value"])
            )
            inline_result = parse_inline_filter(row["inline"])
            expect_ok = row["expect_ok"] == "true"

            self.assertEqual(
                structured.ok,
                expect_ok,
                msg=f"structured parity baseline mismatch for {row['inline']}",
            )
            self.assertEqual(
                inline_result.ok,
                structured.ok,
                msg=f"inline/structured success mismatch for {row['inline']}",
            )

            if expect_ok:
                if structured.ok and inline_result.ok:
                    self.assertEqual(
                        str(inline_result.rule),
                        str(structured.rule),
                        msg=f"inline/structured rule mismatch for {row['inline']}",
                    )
                    expect_rule(
                        self,
                        inline_result.rule,
                        row["expected_field"],
                        row["expected_op"],
                        row["value_kind"],
                        row["expected_value"],
                    )
                continue

            if not structured.ok and not inline_result.ok:
                expected = parse_error_code_name(row["error_code"])
                self.assertEqual(
                    structured.error.code,
                    expected,
                    msg=f"structured error mismatch for {row['inline']}",
                )
                self.assertEqual(
                    inline_result.error.code,
                    structured.error.code,
                    msg=f"inline/structured error mismatch for {row['inline']}",
                )


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
