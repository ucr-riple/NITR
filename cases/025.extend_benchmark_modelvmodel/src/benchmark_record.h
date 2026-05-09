#pragma once

#include <string>

namespace nitr::case025 {

struct BenchmarkRecord {
  std::string model_name;
  std::string family;
  double average_precision = 0.0;
  double fps = 0.0;
};

}  // namespace nitr::case025
