from __future__ import annotations

from src.product import Product
from src.summary_engine import InventorySummary, SummaryEngine


class InventoryReportService:
    def __init__(self, engine: SummaryEngine) -> None:
        if engine is None:
            raise ValueError("engine must not be None")
        self._engine = engine
        self._products: list[Product] = []

    def replace_products(self, products: list[Product]) -> None:
        self._products = list(products)

    def upsert_product(self, product: Product) -> None:
        for index, existing in enumerate(self._products):
            if existing.sku == product.sku:
                self._products[index] = product
                return
        self._products.append(product)

    def clear_cache(self) -> None:
        pass

    def get_summary(self) -> InventorySummary:
        return self._engine.compute(self._products)
