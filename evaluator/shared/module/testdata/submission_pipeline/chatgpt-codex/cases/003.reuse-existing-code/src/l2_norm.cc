#include "l2_norm.h"

#include <cmath>

namespace nitr::case003 {

double L2Norm(std::span<const double> v) {
  double sum_sq = 0.0;
  for (double x : v) {
    sum_sq += x * x;
  }
  return std::sqrt(sum_sq);
}

}  // namespace nitr::case003
