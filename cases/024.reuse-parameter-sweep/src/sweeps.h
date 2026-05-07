#pragma once
#include <vector>
#include "aggregate.h"
#include "runner.h"

namespace nitr::case024 {

struct SweepResult {
  std::vector<TrialParams> configs;
  std::vector<TrialResult> results;
  size_t best_idx = 0;
  SweepSummary summary;
};

// Sweep over a grid of learning rates.
SweepResult sweep_learning_rate(const TrialParams& base,
                                const std::vector<double>& lr_grid);

// Sweep over a 2-D grid of batch sizes and learning rates.
SweepResult sweep_batch_size_x_lr(const TrialParams& base,
                                  const std::vector<int>& batch_sizes,
                                  const std::vector<double>& lr_grid);

// Sweep over a 2-D grid of warmup step counts and learning rates.
SweepResult sweep_warmup_x_lr(const TrialParams& base,
                               const std::vector<int>& warmup_steps_grid,
                               const std::vector<double>& lr_grid);

}  // namespace nitr::case024
