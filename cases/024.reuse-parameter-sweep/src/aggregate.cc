#include "aggregate.h"
#include <stdexcept>

namespace nitr::case024 {

SweepSummary compute_summary(const std::vector<TrialResult>& results) {
  if (results.empty()) {
    throw std::invalid_argument("results must not be empty");
  }
  double sum = 0.0;
  double mn = results[0].loss;
  double mx = results[0].loss;
  for (const auto& r : results) {
    sum += r.loss;
    if (r.loss < mn) { mn = r.loss; }
    if (r.loss > mx) { mx = r.loss; }
  }
  return SweepSummary{sum / static_cast<double>(results.size()), mn, mx};
}

size_t pick_best(const std::vector<TrialResult>& results) {
  if (results.empty()) {
    throw std::invalid_argument("results must not be empty");
  }
  size_t best = 0;
  for (size_t i = 1; i < results.size(); ++i) {
    if (results[i].loss < results[best].loss) { best = i; }
  }
  return best;
}

}  // namespace nitr::case024
