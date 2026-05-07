#pragma once
#include <cstddef>
#include <vector>
#include "runner.h"

namespace nitr::case024 {

struct SweepSummary {
  double mean = 0.0;
  double min_loss = 0.0;
  double max_loss = 0.0;
};

// Compute mean, min, and max loss across a result set.
// Throws std::invalid_argument if results is empty.
SweepSummary compute_summary(const std::vector<TrialResult>& results);

// Return the index of the result with the minimum loss.
// Throws std::invalid_argument if results is empty.
size_t pick_best(const std::vector<TrialResult>& results);

}  // namespace nitr::case024
