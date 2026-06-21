#pragma once
#include <span>

namespace nitr::case003 {

// Returns cosine similarity between vectors a and b.
// - Throws std::invalid_argument if sizes differ.
// - Returns 0.0 if either vector has zero L2 norm.
double CosineSimilarity(std::span<const double> a, std::span<const double> b);

}  // namespace nitr::case003
