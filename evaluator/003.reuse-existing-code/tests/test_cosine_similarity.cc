#include <cmath>
#include <vector>

#include <gtest/gtest.h>

#include "cosine_similarity.h"

static bool NearlyEqual(double a, double b, double eps = 1e-12) {
  return std::fabs(a - b) <= eps;
}

TEST(Case003ReuseExistingCode, ComputesCosineSimilarity) {
  std::vector<double> a{1, 2, 3};
  std::vector<double> b{4, 5, 6};
  const double got = nitr::case003::CosineSimilarity(a, b);
  // expected = dot / (||a|| ||b||)
  const double expected = (1 * 4 + 2 * 5 + 3 * 6) /
                          (std::sqrt(1 + 4 + 9) * std::sqrt(16 + 25 + 36));
  EXPECT_TRUE(NearlyEqual(got, expected));
}

TEST(Case003ReuseExistingCode, OrthogonalVectorsAreZero) {
  std::vector<double> a{1, 0};
  std::vector<double> b{0, 2};
  EXPECT_TRUE(NearlyEqual(nitr::case003::CosineSimilarity(a, b), 0.0));
}

TEST(Case003ReuseExistingCode, SizeMismatchThrowsInvalidArgument) {
  std::vector<double> a{1};
  std::vector<double> b{1, 2};
  EXPECT_THROW((void)nitr::case003::CosineSimilarity(a, b), std::invalid_argument);
}

TEST(Case003ReuseExistingCode, ZeroVectorReturnsZero) {
  std::vector<double> a{0, 0, 0};
  std::vector<double> b{1, 2, 3};
  EXPECT_TRUE(NearlyEqual(nitr::case003::CosineSimilarity(a, b), 0.0));
}
