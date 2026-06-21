#include <iostream>
#include <vector>

#include "cosine_similarity.h"

int main() {
  std::vector<double> a{1.0, 2.0, 3.0};
  std::vector<double> b{4.0, 5.0, 6.0};
  std::cout << nitr::case003::CosineSimilarity(a, b) << std::endl;
  return 0;
}
