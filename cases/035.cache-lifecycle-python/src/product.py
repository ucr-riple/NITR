from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    sku: str
    units_in_stock: int = 0
    reorder_threshold: int = 0
    unit_price: float = 0.0
