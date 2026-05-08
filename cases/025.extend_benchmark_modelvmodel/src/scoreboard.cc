#include "scoreboard.h"

#include <algorithm>

namespace nitr::case025 {

const BenchmarkRecord* FindHighestAccuracy(
    const std::vector<BenchmarkRecord>& records) {
  if (records.empty()) {
    return nullptr;
  }

  return &*std::max_element(
      records.begin(), records.end(),
      [](const BenchmarkRecord& lhs, const BenchmarkRecord& rhs) {
        return lhs.average_precision < rhs.average_precision;
      });
}

std::vector<ScoreEntry> RankByAccuracy(
    const std::vector<BenchmarkRecord>& records) {
  std::vector<ScoreEntry> entries;
  entries.reserve(records.size());

  for (const auto& record : records) {
    entries.push_back({record.model_name, record.average_precision});
  }

  std::sort(entries.begin(), entries.end(),
            [](const ScoreEntry& lhs, const ScoreEntry& rhs) {
              if (lhs.score == rhs.score) {
                return lhs.model_name < rhs.model_name;
              }
              return lhs.score > rhs.score;
            });

  return entries;
}

}  // namespace nitr::case025
