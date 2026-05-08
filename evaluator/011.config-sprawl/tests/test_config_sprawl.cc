#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

#include "report_renderer.h"
#include "report_types.h"

namespace {

bool ExpectEqual(const std::string& actual, const std::string& expected,
                 const std::string& test_name) {
  if (actual != expected) {
    std::cerr << "[FAIL] " << test_name << "\n";
    std::cerr << "Expected:\n" << expected << "\n";
    std::cerr << "Actual:\n" << actual << "\n";
    return false;
  }
  std::cout << "[PASS] " << test_name << "\n";
  return true;
}

}  // namespace

int main() {
  bool ok = true;

  const std::vector<nitr::case011::Item> items = nitr::case011::SampleItems();

  nitr::case011::ReportOptions full_options;
  full_options.include_summary = true;
  const std::string expected_full =
      "Inventory Report\n"
      "Items: 3\n"
      "- id=A-1, name=apple, qty=5\n"
      "- id=B-2, name=banana, qty=2\n"
      "- id=C-3, name=carrot, qty=7\n"
      "Summary\n"
      "Total quantity: 14\n";
  ok = ExpectEqual(nitr::case011::RenderInventoryReport(items, full_options),
                   expected_full, "full mode remains unchanged") &&
       ok;

  nitr::case011::ReportOptions compact_options;
  compact_options.include_summary = true;
  compact_options.compact_mode = true;
  const std::string expected_compact =
      "Inventory Report (compact)\n"
      "A-1:apple:5\n"
      "B-2:banana:2\n"
      "C-3:carrot:7\n"
      "Total quantity: 14\n";
  ok = ExpectEqual(nitr::case011::RenderInventoryReport(items, compact_options),
                   expected_compact, "compact mode renders correctly") &&
       ok;

  nitr::case011::ReportOptions compact_no_summary;
  compact_no_summary.include_summary = false;
  compact_no_summary.compact_mode = true;
  const std::string expected_compact_no_summary =
      "Inventory Report (compact)\n"
      "A-1:apple:5\n"
      "B-2:banana:2\n"
      "C-3:carrot:7\n";
  ok = ExpectEqual(
           nitr::case011::RenderInventoryReport(items, compact_no_summary),
           expected_compact_no_summary,
           "compact mode omits summary when requested") &&
       ok;

  return ok ? EXIT_SUCCESS : EXIT_FAILURE;
}
