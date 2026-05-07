#pragma once
#include <stdexcept>

namespace nitr::case024 {

struct TrialParams {
  int seed = 0;
  double learning_rate = 0.01;
  int batch_size = 32;
  int warmup_steps = 0;
};

struct TrialResult {
  double loss = 0.0;
};

// Execute one parameterised trial and return the result.
// Throws std::invalid_argument on invalid params.
TrialResult run_trial(const TrialParams& params);

}  // namespace nitr::case024
