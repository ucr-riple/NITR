from pathlib import Path
import sys

ROOT = (
    Path(__file__).resolve().parents[3]
    / "cases"
    / Path(__file__).resolve().parents[1].name
)
SERVICE_CC = ROOT / "src" / "report_export_service.cc"
SERVICE_H = ROOT / "src" / "report_export_service.h"
FACTORY_CC = ROOT / "src" / "exporter_factory.cc"

service_text = SERVICE_CC.read_text()
service_header = SERVICE_H.read_text()
factory_text = FACTORY_CC.read_text()
combined_service = service_text + "\n" + service_header

problems = []

lower_service = combined_service.lower()
if "markdown" in lower_service:
    problems.append(
        "report_export_service should remain format-agnostic and must not mention markdown."
    )

if "md" in lower_service:
    problems.append("report_export_service should not add md-specific handling.")

for token in [
    "MarkdownReportExporter",
    "markdown_report_exporter.h",
    "markdown_report_exporter.cc",
]:
    if token in combined_service:
        problems.append(
            "report_export_service should not depend directly on markdown exporter implementation."
        )

if "CreateDefaultExporters" not in factory_text:
    problems.append("factory file looks malformed.")

if problems:
    for problem in problems:
        print(problem)
    sys.exit(1)

print("Structural checks passed.")
