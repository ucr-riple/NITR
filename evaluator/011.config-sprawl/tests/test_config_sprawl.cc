#include <gtest/gtest.h>

#include <string>
#include <vector>

#include "report_renderer.h"
#include "report_types.h"

namespace {

const std::string kExpectedFull =
    "Inventory Report\n"
    "Items: 3\n"
    "- id=A-1, name=apple, qty=5\n"
    "- id=B-2, name=banana, qty=2\n"
    "- id=C-3, name=carrot, qty=7\n"
    "Summary\n"
    "Total quantity: 14\n";

const std::string kExpectedCompact =
    "Inventory Report (compact)\n"
    "A-1:apple:5\n"
    "B-2:banana:2\n"
    "C-3:carrot:7\n"
    "Total quantity: 14\n";

const std::string kExpectedCompactNoSummary =
    "Inventory Report (compact)\n"
    "A-1:apple:5\n"
    "B-2:banana:2\n"
    "C-3:carrot:7\n";

}  // namespace

TEST(Case011ConfigSprawl, RendersAllModes) {
  const std::vector<nitr::case011::Item> items = nitr::case011::SampleItems();

  nitr::case011::ReportOptions full_options;
  full_options.include_summary = true;
  EXPECT_EQ(nitr::case011::RenderInventoryReport(items, full_options),
            kExpectedFull);

  nitr::case011::ReportOptions compact_options;
  compact_options.include_summary = true;
  compact_options.compact_mode = true;
  EXPECT_EQ(nitr::case011::RenderInventoryReport(items, compact_options),
            kExpectedCompact);

  nitr::case011::ReportOptions compact_no_summary;
  compact_no_summary.include_summary = false;
  compact_no_summary.compact_mode = true;
  EXPECT_EQ(nitr::case011::RenderInventoryReport(items, compact_no_summary),
            kExpectedCompactNoSummary);
}
