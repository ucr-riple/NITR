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

from src.inventory_report_service import InventoryReportService
from src.product import Product
from src.summary_engine import InventorySummary, SummaryEngine


class CountingSummaryEngine(SummaryEngine):
    def __init__(self) -> None:
        self.compute_calls = 0

    def compute(self, products: list[Product]) -> InventorySummary:
        self.compute_calls += 1
        low_stock_count = sum(
            product.units_in_stock <= product.reorder_threshold for product in products
        )
        inventory_value = sum(
            product.units_in_stock * product.unit_price for product in products
        )
        return InventorySummary(len(products), low_stock_count, inventory_value)


def initial_products() -> list[Product]:
    return [
        Product("A-100", 10, 3, 2.5),
        Product("B-200", 2, 5, 10.0),
    ]


class ReportCacheTests(unittest.TestCase):
    def test_caches_repeated_summary_reads(self) -> None:
        engine = CountingSummaryEngine()
        service = InventoryReportService(engine)
        service.replace_products(initial_products())

        first = service.get_summary()
        second = service.get_summary()

        self.assertEqual(engine.compute_calls, 1)
        self.assertEqual(first, InventorySummary(2, 1, 45.0))
        self.assertEqual(second, first)

    def test_replacing_products_invalidates_cache(self) -> None:
        engine = CountingSummaryEngine()
        service = InventoryReportService(engine)
        service.replace_products(initial_products())
        service.get_summary()

        service.replace_products([Product("C-300", 1, 2, 7.0)])
        summary = service.get_summary()

        self.assertEqual(engine.compute_calls, 2)
        self.assertEqual(summary, InventorySummary(1, 1, 7.0))

    def test_updating_product_invalidates_cache(self) -> None:
        engine = CountingSummaryEngine()
        service = InventoryReportService(engine)
        service.replace_products(initial_products())
        service.get_summary()

        service.upsert_product(Product("B-200", 8, 5, 10.0))
        summary = service.get_summary()

        self.assertEqual(engine.compute_calls, 2)
        self.assertEqual(summary, InventorySummary(2, 0, 105.0))

    def test_inserting_product_invalidates_cache(self) -> None:
        engine = CountingSummaryEngine()
        service = InventoryReportService(engine)
        service.replace_products(initial_products())
        service.get_summary()

        service.upsert_product(Product("C-300", 1, 2, 7.0))
        summary = service.get_summary()

        self.assertEqual(engine.compute_calls, 2)
        self.assertEqual(summary, InventorySummary(3, 2, 52.0))

    def test_clear_cache_forces_recompute(self) -> None:
        engine = CountingSummaryEngine()
        service = InventoryReportService(engine)
        service.replace_products(initial_products())
        service.get_summary()

        service.clear_cache()
        service.get_summary()

        self.assertEqual(engine.compute_calls, 2)

    def test_cache_is_owned_per_service_instance(self) -> None:
        engine = CountingSummaryEngine()
        first_service = InventoryReportService(engine)
        second_service = InventoryReportService(engine)
        first_service.replace_products(initial_products())
        second_service.replace_products([Product("C-300", 1, 2, 7.0)])

        first_summary = first_service.get_summary()
        second_summary = second_service.get_summary()

        self.assertEqual(engine.compute_calls, 2)
        self.assertEqual(first_summary, InventorySummary(2, 1, 45.0))
        self.assertEqual(second_summary, InventorySummary(1, 1, 7.0))


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
