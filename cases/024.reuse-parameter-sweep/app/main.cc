#include <iostream>
#include <string>
#include <vector>
#include "runner.h"
#include "sweeps.h"

int main(int argc, char** argv) {
  using namespace nitr::case024;

  TrialParams base{};
  base.seed = 42;
  base.learning_rate = 0.01;
  base.batch_size = 32;
  base.warmup_steps = 0;

  const std::vector<double> lr_grid     = {0.001, 0.01, 0.1};
  const std::vector<int>    batch_sizes  = {16, 32, 64};
  const std::vector<int>    warmup_steps = {0, 50, 100, 200};

  if (argc < 2) {
    std::cerr << "Usage: " << argv[0]
              << " <lr|batch_x_lr|warmup_x_lr>\n";
    return 1;
  }

  const std::string cmd = argv[1];
  if (cmd == "lr") {
    auto r = sweep_learning_rate(base, lr_grid);
    std::cout << "best_idx=" << r.best_idx
              << " loss=" << r.results[r.best_idx].loss << "\n";
  } else if (cmd == "batch_x_lr") {
    auto r = sweep_batch_size_x_lr(base, batch_sizes, lr_grid);
    std::cout << "best_idx=" << r.best_idx
              << " loss=" << r.results[r.best_idx].loss << "\n";
  } else if (cmd == "warmup_x_lr") {
    auto r = sweep_warmup_x_lr(base, warmup_steps, lr_grid);
    std::cout << "best_idx=" << r.best_idx
              << " loss=" << r.results[r.best_idx].loss << "\n";
  } else {
    std::cerr << "Unknown command: " << cmd << "\n";
    return 1;
  }
  return 0;
}
