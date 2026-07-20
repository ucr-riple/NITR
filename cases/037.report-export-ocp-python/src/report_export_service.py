from __future__ import annotations

from src.report import Report
from src.report_exporter import ReportExporter


class ReportExportService:
    def __init__(self, exporters: list[ReportExporter]) -> None:
        self._exporters = list(exporters)

    def export_report(self, report: Report, format_key: str) -> str:
        for exporter in self._exporters:
            if exporter.can_handle(format_key):
                return exporter.export(report)
        raise ValueError(f"Unsupported format: {format_key}")
