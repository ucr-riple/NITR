#include <exception>
#include <iostream>
#include <string>

#include "exporter_factory.h"
#include "report_export_service.h"

namespace {

bool ExpectEq(const std::string& actual, const std::string& expected,
              const std::string& label) {
  if (actual != expected) {
    std::cerr << "FAILED: " << label << "\nExpected:\n"
              << expected << "\nActual:\n"
              << actual << "\n";
    return false;
  }
  return true;
}

nitr::case014::Report MakeReport() {
  nitr::case014::Report report;
  report.title = "Quarterly Metrics";
  report.columns = {"Name", "Value"};
  report.rows = {{"Latency", "120ms"}, {"Errors", "3"}};
  return report;
}

}  // namespace

int main() {
  const nitr::case014::Report report = MakeReport();
  nitr::case014::ReportExportService service(
      nitr::case014::CreateDefaultExporters());

  bool ok = true;

  ok = ExpectEq(service.ExportReport(report, "text"),
                "Quarterly Metrics\nName, Value\nLatency, 120ms\nErrors, 3\n",
                "text export") &&
       ok;

  ok = ExpectEq(service.ExportReport(report, "csv"),
                "Name,Value\nLatency,120ms\nErrors,3\n", "csv export") &&
       ok;

  try {
    const std::string markdown = service.ExportReport(report, "markdown");
    ok = ExpectEq(markdown,
                  "# Quarterly Metrics\n\n| Name | Value |\n| --- | --- |\n| "
                  "Latency | 120ms |\n| Errors | 3 |\n",
                  "markdown export") &&
         ok;
  } catch (const std::exception& ex) {
    std::cerr << "FAILED: markdown export threw exception: " << ex.what()
              << "\n";
    ok = false;
  }

  if (!ok) {
    return 1;
  }

  std::cout << "All functional tests passed.\n";
  return 0;
}
