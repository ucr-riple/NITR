from __future__ import annotations

from src.inventory_report_service import InventoryReportService
from src.product import Product
from src.summary_engine import BasicSummaryEngine


def main() -> None:
    service = InventoryReportService(BasicSummaryEngine())
    service.replace_products(
        [
            Product("A-100", 10, 3, 2.5),
            Product("B-200", 2, 5, 10.0),
        ]
    )

    summary = service.get_summary()
    print(
        f"products={summary.product_count}, "
        f"low_stock={summary.low_stock_count}, "
        f"value={summary.inventory_value}"
    )


if __name__ == "__main__":
    main()
