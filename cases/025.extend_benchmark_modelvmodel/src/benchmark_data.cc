#include "benchmark_data.h"

namespace nitr::case025 {

std::vector<BenchmarkRecord> DefaultDetectorBenchmarkRows() {
  return {
      {"D-FINE-Nano", "D-FINE", 42.7, 220.0},
      {"D-FINE-Small", "D-FINE", 48.5, 160.0},
      {"RT-DETR-R18", "RT-DETR", 46.5, 125.0},
      {"RT-DETR-R50", "RT-DETR", 53.1, 108.0},
  };
}

}  // namespace nitr::case025
