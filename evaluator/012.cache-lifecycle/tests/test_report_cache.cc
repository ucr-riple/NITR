#include <cmath>
#include <vector>

#include <gtest/gtest.h>

#include "inventory_report_service.h"
#include "summary_engine.h"

namespace {

class CountingSummaryEngine final : public nitr::case012::SummaryEngine {
 public:
  nitr::case012::InventorySummary Compute(
      const std::vector<nitr::case012::Product>& products) const override {
    compute_calls += 1;

    nitr::case012::InventorySummary summary;
    summary.product_count = static_cast<int>(products.size());
    for (const nitr::case012::Product& product : products) {
      if (product.units_in_stock <= product.reorder_threshold) {
        summary.low_stock_count += 1;
      }
      summary.inventory_value +=
          static_cast<double>(product.units_in_stock) * product.unit_price;
    }
    return summary;
  }

  mutable int compute_calls = 0;
};

bool NearlyEqual(double a, double b) {
  return std::fabs(a - b) < 1e-9;
}

TEST(Case012ReportCache, CachesRepeatedSummaryReads) {
  CountingSummaryEngine engine;
  nitr::case012::InventoryReportService service(&engine);

  service.ReplaceProducts({
      {"A-100", 10, 3, 2.5},
      {"B-200", 2, 5, 10.0},
  });

  const nitr::case012::InventorySummary first = service.GetSummary();
  const nitr::case012::InventorySummary second = service.GetSummary();

  EXPECT_EQ(engine.compute_calls, 1);
  EXPECT_EQ(first.product_count, 2);
  EXPECT_EQ(first.low_stock_count, 1);
  EXPECT_TRUE(NearlyEqual(first.inventory_value, 45.0));
  EXPECT_EQ(second.product_count, first.product_count);
  EXPECT_EQ(second.low_stock_count, first.low_stock_count);
  EXPECT_TRUE(NearlyEqual(second.inventory_value, first.inventory_value));
}

TEST(Case012ReportCache, ReplacingProductsInvalidatesCache) {
  CountingSummaryEngine engine;
  nitr::case012::InventoryReportService service(&engine);

  service.ReplaceProducts({
      {"A-100", 10, 3, 2.5},
      {"B-200", 2, 5, 10.0},
  });
  (void)service.GetSummary();

  service.ReplaceProducts({
      {"C-300", 1, 2, 7.0},
  });
  const nitr::case012::InventorySummary summary = service.GetSummary();

  EXPECT_EQ(engine.compute_calls, 2);
  EXPECT_EQ(summary.product_count, 1);
  EXPECT_EQ(summary.low_stock_count, 1);
  EXPECT_TRUE(NearlyEqual(summary.inventory_value, 7.0));
}

TEST(Case012ReportCache, UpsertingProductInvalidatesCache) {
  CountingSummaryEngine engine;
  nitr::case012::InventoryReportService service(&engine);

  service.ReplaceProducts({
      {"A-100", 10, 3, 2.5},
      {"B-200", 2, 5, 10.0},
  });
  (void)service.GetSummary();

  service.UpsertProduct({"B-200", 8, 5, 10.0});
  const nitr::case012::InventorySummary summary = service.GetSummary();

  EXPECT_EQ(engine.compute_calls, 2);
  EXPECT_EQ(summary.product_count, 2);
  EXPECT_EQ(summary.low_stock_count, 0);
  EXPECT_TRUE(NearlyEqual(summary.inventory_value, 105.0));
}

TEST(Case012ReportCache, ClearCacheForcesRecompute) {
  CountingSummaryEngine engine;
  nitr::case012::InventoryReportService service(&engine);

  service.ReplaceProducts({
      {"A-100", 10, 3, 2.5},
      {"B-200", 2, 5, 10.0},
  });
  (void)service.GetSummary();
  service.ClearCache();
  (void)service.GetSummary();

  EXPECT_EQ(engine.compute_calls, 2);
}

}  // namespace
