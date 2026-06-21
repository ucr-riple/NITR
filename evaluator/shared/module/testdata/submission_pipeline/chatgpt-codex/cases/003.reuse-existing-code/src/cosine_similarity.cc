#include "cosine_similarity.h"

#include <stdexcept>

#include "dot_product.h"
#include "l2_norm.h"

namespace nitr::case003 {

double CosineSimilarity(std::span<const double> a, std::span<const double> b) {
  if (a.size() != b.size()) {
    throw std::invalid_argument("CosineSimilarity: size mismatch");
  }

  const double norm_a = L2Norm(a);
  const double norm_b = L2Norm(b);
  if (norm_a == 0.0 || norm_b == 0.0) {
    return 0.0;
  }

  return DotProduct(a, b) / (norm_a * norm_b);
}

}  // namespace nitr::case003
