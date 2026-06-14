#!/usr/bin/env python3

"""Check structural format-agnostic boundaries for case 014 report export.

Rule:
  - report_export_service should avoid markdown-specific implementation details and
    direct markdown exporter dependencies.

Inputs:
  - `--case_root` (defaults to script's case directory).
  - `src/report_export_service.cc`
  - `src/report_export_service.h`
  - `src/exporter_factory.cc`

Checks:
  - Flag markdown mentions in service implementation/header text.
  - Ensure factory exposes default exporter creation entry point.

Output:
  - emit_check_result with pass/fail findings.
"""

import argparse
from pathlib import Path

from evaluator.shared.path_checks import case_root_from_script, read_text
from evaluator.shared.check_output import emit_check_result


def main() -> int:

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()
    case_root = args.case_root.resolve()

    SERVICE_CC = case_root / "src" / "report_export_service.cc"
    SERVICE_H = case_root / "src" / "report_export_service.h"
    FACTORY_CC = case_root / "src" / "exporter_factory.cc"

    service_text = read_text(SERVICE_CC, missing_ok=False)
    service_header = read_text(SERVICE_H, missing_ok=False)
    factory_text = read_text(FACTORY_CC, missing_ok=False)
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

    return emit_check_result(passed=not problems, findings=problems)


if __name__ == "__main__":
    raise SystemExit(main())
