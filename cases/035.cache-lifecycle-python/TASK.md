# Task

Add summary caching to `InventoryReportService`.

Requirements:

- Repeated `get_summary()` calls should reuse the last computed summary when
  the product collection has not changed.
- `replace_products(...)` should make the old cached summary invalid.
- `upsert_product(...)` should make the old cached summary invalid.
- `clear_cache()` should force the next `get_summary()` call to recompute the
  summary.
- Keep the current behavior of summary values correct after product
  replacement and updates.
