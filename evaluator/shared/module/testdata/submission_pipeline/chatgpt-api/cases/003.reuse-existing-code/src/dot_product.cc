#include "dot_product.h"

#include <stdexcept>

namespace nitr::case003 {

double DotProduct(std::span<const double> a, std::span<const double> b) {
  if (a.size() != b.size()) {
    throw std::invalid_argument("DotProduct: size mismatch");
  }
  double sum = 0.0;
  for (std::size_t i = 0; i < a.size(); ++i) {
    sum += a[i] * b[i];
  }
  return sum;
}

}  // namespace nitr::case003
