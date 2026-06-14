#include <string>

#include <gtest/gtest.h>

#include "exporter_factory.h"
#include "report_export_service.h"

namespace {

[[nodiscard]] nitr::case014::Report MakeReport() {
  nitr::case014::Report report;
  report.title = "Quarterly Metrics";
  report.columns = {"Name", "Value"};
  report.rows = {{"Latency", "120ms"}, {"Errors", "3"}};
  return report;
}

}  // namespace

TEST(Case014ReportExport, ExportsText) {
  const nitr::case014::Report report = MakeReport();
  nitr::case014::ReportExportService service(
      nitr::case014::CreateDefaultExporters());

  EXPECT_EQ(
      service.ExportReport(report, "text"),
      "Quarterly Metrics\nName, Value\nLatency, 120ms\nErrors, 3\n"
  );
}

TEST(Case014ReportExport, ExportsCsv) {
  const nitr::case014::Report report = MakeReport();
  nitr::case014::ReportExportService service(
      nitr::case014::CreateDefaultExporters());

  EXPECT_EQ(service.ExportReport(report, "csv"),
            "Name,Value\nLatency,120ms\nErrors,3\n");
}

TEST(Case014ReportExport, ExportsMarkdown) {
  const nitr::case014::Report report = MakeReport();
  nitr::case014::ReportExportService service(
      nitr::case014::CreateDefaultExporters());

  EXPECT_NO_THROW({
    const std::string markdown = service.ExportReport(report, "markdown");
    EXPECT_EQ(markdown,
              "# Quarterly Metrics\n\n| Name | Value |\n| --- | --- |"
              "\n| Latency | 120ms |\n| Errors | 3 |\n");
  });
}
