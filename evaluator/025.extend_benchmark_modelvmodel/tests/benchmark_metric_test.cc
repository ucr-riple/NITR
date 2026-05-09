#include <gtest/gtest.h>

#include "benchmark_data.h"
#include "benchmark_runner.h"
#include "benchmark_record.h"

#include <vector>

TEST(BenchmarkMetricTest, KeepsAccuracyWinnerBehavior) {
  const std::vector<nitr::case025::BenchmarkRecord> rows = {
      {"D-FINE-Nano", "D-FINE", 42.7, 220.0},
      {"D-FINE-Small", "D-FINE", 48.5, 160.0},
      {"RT-DETR-R50", "RT-DETR", 53.1, 108.0},
  };

  const auto summary = nitr::case025::RunBenchmark(rows);

  EXPECT_EQ(summary.accuracy_winner, "RT-DETR-R50");
  ASSERT_FALSE(summary.accuracy_ranking.empty());
  EXPECT_EQ(summary.accuracy_ranking.front().model_name, "RT-DETR-R50");
}

TEST(BenchmarkMetricTest, ReportsSpeedAdjustedWinner) {
  const std::vector<nitr::case025::BenchmarkRecord> rows = {
      {"D-FINE-Nano", "D-FINE", 42.7, 220.0},
      {"D-FINE-Small", "D-FINE", 48.5, 160.0},
      {"RT-DETR-R50", "RT-DETR", 53.1, 108.0},
  };

  const auto summary = nitr::case025::RunBenchmark(rows);

  EXPECT_EQ(summary.speed_adjusted_winner, "D-FINE-Nano");
  ASSERT_FALSE(summary.speed_adjusted_ranking.empty());
  EXPECT_EQ(summary.speed_adjusted_ranking.front().model_name, "D-FINE-Nano");
  EXPECT_NEAR(summary.speed_adjusted_ranking.front().score, 93.94, 1e-9);
}

TEST(BenchmarkMetricTest, SupportsDefaultDfineAndRtDetrRows) {
  const auto summary =
      nitr::case025::RunBenchmark(nitr::case025::DefaultDetectorBenchmarkRows());

  EXPECT_EQ(summary.accuracy_winner, "RT-DETR-R50");
  EXPECT_EQ(summary.speed_adjusted_winner, "D-FINE-Nano");
}

TEST(BenchmarkMetricTest, FormatsBothWinners) {
  nitr::case025::BenchmarkSummary summary;
  summary.accuracy_winner = "RT-DETR-R50";
  summary.speed_adjusted_winner = "D-FINE-Nano";

  const std::string formatted = nitr::case025::FormatSummary(summary);

  EXPECT_NE(formatted.find("Accuracy winner: RT-DETR-R50"),
            std::string::npos);
  EXPECT_NE(formatted.find("Speed-adjusted winner: D-FINE-Nano"),
            std::string::npos);
}
