#pragma once

#include <string>
#include <vector>

#include "benchmark_record.h"

namespace nitr::case025 {

struct ScoreEntry {
  std::string model_name;
  double score = 0.0;
};

const BenchmarkRecord* FindHighestAccuracy(
    const std::vector<BenchmarkRecord>& records);

std::vector<ScoreEntry> RankByAccuracy(
    const std::vector<BenchmarkRecord>& records);

}  // namespace nitr::case025
