from __future__ import annotations

from src.report import Report
from src.report_exporter import ReportExporter


class TextReportExporter(ReportExporter):
    def can_handle(self, format_key: str) -> bool:
        return format_key == "text"

    def export(self, report: Report) -> str:
        output = f"{report.title}\n"
        output += ", ".join(report.columns) + "\n"
        for row in report.rows:
            output += ", ".join(row) + "\n"
        return output
