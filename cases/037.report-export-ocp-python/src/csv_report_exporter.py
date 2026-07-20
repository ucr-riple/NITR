from __future__ import annotations

from src.report import Report
from src.report_exporter import ReportExporter


class CsvReportExporter(ReportExporter):
    def can_handle(self, format_key: str) -> bool:
        return format_key == "csv"

    def export(self, report: Report) -> str:
        output = ",".join(report.columns) + "\n"
        for row in report.rows:
            output += ",".join(row) + "\n"
        return output
