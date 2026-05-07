#include "sweeps.h"

namespace nitr::case024 {

SweepResult sweep_learning_rate(const TrialParams& base,
                                const std::vector<double>& lr_grid) {
  SweepResult out;
  for (double lr : lr_grid) {
    TrialParams p = base;
    p.learning_rate = lr;
    out.configs.push_back(p);
    out.results.push_back(run_trial(p));
  }
  out.best_idx = pick_best(out.results);
  out.summary   = compute_summary(out.results);
  return out;
}

SweepResult sweep_batch_size_x_lr(const TrialParams& base,
                                  const std::vector<int>& batch_sizes,
                                  const std::vector<double>& lr_grid) {
  SweepResult out;
  for (int bs : batch_sizes) {
    for (double lr : lr_grid) {
      TrialParams p = base;
      p.batch_size   = bs;
      p.learning_rate = lr;
      out.configs.push_back(p);
      out.results.push_back(run_trial(p));
    }
  }
  out.best_idx = pick_best(out.results);
  out.summary   = compute_summary(out.results);
  return out;
}

SweepResult sweep_warmup_x_lr(const TrialParams& base,
                               const std::vector<int>& warmup_steps_grid,
                               const std::vector<double>& lr_grid) {
  SweepResult out;
  for (int ws : warmup_steps_grid) {
    for (double lr : lr_grid) {
      TrialParams p = base;
      p.warmup_steps  = ws;
      p.learning_rate = lr;
      out.configs.push_back(p);
      out.results.push_back(run_trial(p));
    }
  }
  out.best_idx = pick_best(out.results);
  out.summary   = compute_summary(out.results);
  return out;
}

}  // namespace nitr::case024
