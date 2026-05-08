#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

#include "cosine_similarity.h"

static bool NearlyEqual(double a, double b, double eps = 1e-12) {
  return std::fabs(a - b) <= eps;
}

int main() {
  {  // basic
    std::vector<double> a{1, 2, 3};
    std::vector<double> b{4, 5, 6};
    const double got = nitr::case003::CosineSimilarity(a, b);
    // expected = dot / (||a|| ||b||)
    const double expected = (1 * 4 + 2 * 5 + 3 * 6) /
                            (std::sqrt(1 + 4 + 9) * std::sqrt(16 + 25 + 36));
    assert(NearlyEqual(got, expected));
  }

  {  // orthogonal
    std::vector<double> a{1, 0};
    std::vector<double> b{0, 2};
    assert(NearlyEqual(nitr::case003::CosineSimilarity(a, b), 0.0));
  }

  {  // size mismatch
    std::vector<double> a{1};
    std::vector<double> b{1, 2};
    bool threw = false;
    try {
      (void)nitr::case003::CosineSimilarity(a, b);
    } catch (const std::invalid_argument&) {
      threw = true;
    }
    assert(threw);
  }

  {  // zero vector -> 0
    std::vector<double> a{0, 0, 0};
    std::vector<double> b{1, 2, 3};
    assert(NearlyEqual(nitr::case003::CosineSimilarity(a, b), 0.0));
  }

  std::cout << "Functional tests passed." << std::endl;
  return 0;
}
