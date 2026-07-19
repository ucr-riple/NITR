from __future__ import annotations

from src.report_renderer import render_inventory_report
from src.report_types import ReportOptions, sample_items


def main() -> None:
    items = sample_items()
    full_options = ReportOptions(include_summary=True)

    print("=== Full Report ===")
    print(render_inventory_report(items, full_options))

    print("=== Compact Report ===")
    print("Compact mode not implemented yet.")


if __name__ == "__main__":
    main()
