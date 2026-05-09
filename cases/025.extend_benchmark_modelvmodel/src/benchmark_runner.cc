#include "benchmark_runner.h"

#include <sstream>

namespace nitr::case025 {

BenchmarkSummary RunBenchmark(const std::vector<BenchmarkRecord>& records) {
  BenchmarkSummary summary;

  const BenchmarkRecord* accuracy_winner = FindHighestAccuracy(records);
  if (accuracy_winner != nullptr) {
    summary.accuracy_winner = accuracy_winner->model_name;
  }

  summary.accuracy_ranking = RankByAccuracy(records);
  // Needs Implementation
  return summary;
}

std::string FormatSummary(const BenchmarkSummary& summary) {
  std::ostringstream out;
  out << "Accuracy winner: " << summary.accuracy_winner << "\n";
  // Needs Implementation
  return out.str();
}

}  // namespace nitr::case025
