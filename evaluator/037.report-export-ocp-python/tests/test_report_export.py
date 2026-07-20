#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

ARG_PARSER = argparse.ArgumentParser()
ARG_PARSER.add_argument("--case_root", required=True)
ARGS = ARG_PARSER.parse_args()

CASE_ROOT = Path(ARGS.case_root).resolve()
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.exporter_factory import create_default_exporters
from src.report import Report
from src.report_export_service import ReportExportService
from src.report_exporter import ReportExporter


def make_report() -> Report:
    return Report(
        title="Quarterly Metrics",
        columns=["Name", "Value"],
        rows=[["Latency", "120ms"], ["Errors", "3"]],
    )


class StubReportExporter(ReportExporter):
    def can_handle(self, format_key: str) -> bool:
        return format_key == "stub"

    def export(self, report: Report) -> str:
        return f"stub:{report.title}"


class ReportExportTests(unittest.TestCase):
    def test_exports_text(self) -> None:
        service = ReportExportService(create_default_exporters())

        self.assertEqual(
            service.export_report(make_report(), "text"),
            "Quarterly Metrics\nName, Value\nLatency, 120ms\nErrors, 3\n",
        )

    def test_exports_csv(self) -> None:
        service = ReportExportService(create_default_exporters())

        self.assertEqual(
            service.export_report(make_report(), "csv"),
            "Name,Value\nLatency,120ms\nErrors,3\n",
        )

    def test_exports_markdown(self) -> None:
        service = ReportExportService(create_default_exporters())

        self.assertEqual(
            service.export_report(make_report(), "markdown"),
            "# Quarterly Metrics\n\n"
            "| Name | Value |\n"
            "| --- | --- |\n"
            "| Latency | 120ms |\n"
            "| Errors | 3 |\n",
        )

    def test_rejects_unsupported_format(self) -> None:
        service = ReportExportService(create_default_exporters())

        with self.assertRaisesRegex(ValueError, "^Unsupported format: yaml$"):
            service.export_report(make_report(), "yaml")

    def test_service_accepts_an_injected_exporter(self) -> None:
        service = ReportExportService([StubReportExporter()])

        self.assertEqual(
            service.export_report(make_report(), "stub"),
            "stub:Quarterly Metrics",
        )


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
