#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import unittest
from pathlib import Path

ARG_PARSER = argparse.ArgumentParser()
ARG_PARSER.add_argument("--case_root", required=True)
ARGS = ARG_PARSER.parse_args()

CASE_ROOT = Path(ARGS.case_root).resolve()
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.pricing import (
    DEFAULT_RULE_REGISTRY,
    Discount,
    Order,
    PricingRule,
    RuleContext,
    compute_final_price,
)


def order(
    subtotal: float,
    is_member: bool = False,
    items: int = 0,
    coupons: tuple[str, ...] = (),
) -> Order:
    return Order(round(subtotal * 100), is_member, items, coupons)


class InjectedRule(PricingRule):
    @property
    def rule_id(self) -> str:
        return "INJECTED_10P"

    def applicable(self, context: RuleContext) -> bool:
        return "INJECTED" in set(context.order.coupons)

    def discount(self, context: RuleContext) -> Discount:
        return Discount(percent=0.10)


class PricingTests(unittest.TestCase):
    def test_m1_rules_and_aggregation(self) -> None:
        self.assertEqual(compute_final_price(order(120), 1).final_price_cents, 12000)
        result = compute_final_price(order(120, True, 10), 1)
        self.assertEqual(result.final_price_cents, 8800)
        self.assertEqual(result.applied_rules, ["ITEMS_20OFF", "MEMBER_10P"])

    def test_m2_coupons_are_a_set(self) -> None:
        result = compute_final_price(
            order(100, coupons=("SAVE5", "SAVE5", "SAVE10P")), 2
        )
        self.assertEqual(result.final_price_cents, 8500)
        self.assertEqual(
            result.applied_rules, ["COUPON_SAVE10P", "COUPON_SAVE5"]
        )

    def test_m3_coupon_group_exclusivity(self) -> None:
        result = compute_final_price(
            order(120, True, 10, ("SAVE5", "SAVE10P")), 3
        )
        self.assertEqual(result.final_price_cents, 7600)
        self.assertEqual(
            result.applied_rules,
            ["ITEMS_20OFF", "MEMBER_10P", "COUPON_SAVE10P"],
        )

    def test_runtime_rule_disables_member(self) -> None:
        data_path = (
            Path(__file__).resolve().parents[1] / "data" / "runtime_rules.json"
        )
        previous = os.environ.get("NITR_RULES")
        os.environ["NITR_RULES"] = str(data_path)
        try:
            result = compute_final_price(
                order(100, True, 12, ("BLACKFRIDAY", "SAVE10P")), 4
            )
        finally:
            if previous is None:
                os.environ.pop("NITR_RULES", None)
            else:
                os.environ["NITR_RULES"] = previous
        self.assertEqual(result.final_price_cents, 5000)
        self.assertEqual(result.applied_rules, ["ITEMS_20OFF", "BLACKFRIDAY_30P"])

    def test_external_rule_extends_without_core_changes(self) -> None:
        DEFAULT_RULE_REGISTRY.register("evaluator-injected", lambda _: InjectedRule())

        result = compute_final_price(order(100, coupons=("INJECTED",)), 4)

        self.assertEqual(result.final_price_cents, 9000)
        self.assertIn("INJECTED_10P", result.applied_rules)

    def test_unknown_coupon_is_ignored(self) -> None:
        result = compute_final_price(order(42, coupons=("UNKNOWN",)), 2)
        self.assertEqual(result.final_price_cents, 4200)

    def test_invalid_runtime_rules_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rules.json"
            path.write_text(
                '{"rules":[{"id":"BAD","type":"percent","value":1.5}]}',
                encoding="utf-8",
            )
            previous = os.environ.get("NITR_RULES")
            os.environ["NITR_RULES"] = str(path)
            try:
                with self.assertRaisesRegex(RuntimeError, "ERR_INVALID_SCHEMA"):
                    compute_final_price(order(100), 4)
            finally:
                if previous is None:
                    os.environ.pop("NITR_RULES", None)
                else:
                    os.environ["NITR_RULES"] = previous


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
