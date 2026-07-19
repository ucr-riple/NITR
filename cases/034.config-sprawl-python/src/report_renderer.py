from __future__ import annotations

from src.report_types import Item, ReportOptions


def _render_header(items: list[Item]) -> str:
    return f"Inventory Report\nItems: {len(items)}\n"


def _render_row(item: Item) -> str:
    return f"- id={item.id}, name={item.name}, qty={item.quantity}\n"


def _total_quantity(items: list[Item]) -> int:
    return sum(item.quantity for item in items)


def _render_footer(items: list[Item], options: ReportOptions) -> str:
    if not options.include_summary:
        return ""
    return f"Summary\nTotal quantity: {_total_quantity(items)}\n"


def render_inventory_report(items: list[Item], options: ReportOptions) -> str:
    output = _render_header(items)
    output += "".join(_render_row(item) for item in items)
    output += _render_footer(items, options)
    return output
