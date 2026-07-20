from __future__ import annotations

from src.csv_report_exporter import CsvReportExporter
from src.report_exporter import ReportExporter
from src.text_report_exporter import TextReportExporter


def create_default_exporters() -> list[ReportExporter]:
    return [TextReportExporter(), CsvReportExporter()]
