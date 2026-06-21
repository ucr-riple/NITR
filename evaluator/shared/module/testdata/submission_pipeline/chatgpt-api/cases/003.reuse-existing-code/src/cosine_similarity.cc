#include "cosine_similarity.h"

#include <stdexcept>

#include "dot_product.h"
#include "l2_norm.h"

namespace nitr::case003 {

double CosineSimilarity(std::span<const double> a, std::span<const double> b) {
  if (a.size() != b.size()) {
    throw std::invalid_argument("CosineSimilarity: size mismatch");
  }

  const double l2a = L2Norm(a);
  const double l2b = L2Norm(b);
  if (l2a == 0.0 || l2b == 0.0) {
    return 0.0;
  }

  const double dp = DotProduct(a, b);
  return dp / (l2a * l2b);
}

}  // namespace nitr::case003
