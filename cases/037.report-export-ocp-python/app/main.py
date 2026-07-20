from __future__ import annotations

from src.exporter_factory import create_default_exporters
from src.report import Report
from src.report_export_service import ReportExportService


def main() -> None:
    report = Report(
        title="Quarterly Metrics",
        columns=["Name", "Value"],
        rows=[["Latency", "120ms"], ["Errors", "3"]],
    )
    service = ReportExportService(create_default_exporters())
    print(service.export_report(report, "text"), end="")


if __name__ == "__main__":
    main()
