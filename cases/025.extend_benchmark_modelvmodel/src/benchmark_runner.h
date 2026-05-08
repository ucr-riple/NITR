#pragma once

#include <string>
#include <vector>

#include "benchmark_record.h"
#include "scoreboard.h"

namespace nitr::case025 {

struct BenchmarkSummary {
  std::string accuracy_winner;
  std::string speed_adjusted_winner;
  std::vector<ScoreEntry> accuracy_ranking;
  std::vector<ScoreEntry> speed_adjusted_ranking;
};

BenchmarkSummary RunBenchmark(const std::vector<BenchmarkRecord>& records);

std::string FormatSummary(const BenchmarkSummary& summary);

}  // namespace nitr::case025
