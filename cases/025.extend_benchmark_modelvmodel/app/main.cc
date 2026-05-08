#include <iostream>

#include "benchmark_data.h"
#include "benchmark_runner.h"

int main() {
  const auto rows = nitr::case025::DefaultDetectorBenchmarkRows();
  const auto summary = nitr::case025::RunBenchmark(rows);
  std::cout << nitr::case025::FormatSummary(summary);
  return 0;
}
