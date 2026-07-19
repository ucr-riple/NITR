from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.product import Product


@dataclass(frozen=True)
class InventorySummary:
    product_count: int = 0
    low_stock_count: int = 0
    inventory_value: float = 0.0


class SummaryEngine(ABC):
    @abstractmethod
    def compute(self, products: list[Product]) -> InventorySummary:
        """Compute a summary for the supplied product collection."""


class BasicSummaryEngine(SummaryEngine):
    def compute(self, products: list[Product]) -> InventorySummary:
        low_stock_count = sum(
            product.units_in_stock <= product.reorder_threshold
            for product in products
        )
        inventory_value = sum(
            product.units_in_stock * product.unit_price for product in products
        )
        return InventorySummary(len(products), low_stock_count, inventory_value)
