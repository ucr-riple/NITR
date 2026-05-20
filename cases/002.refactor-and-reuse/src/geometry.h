#pragma once

#include <array>
#include <vector>

namespace nitr::case002 {
struct Vec2 {
  double x = 0.0;
  double y = 0.0;
};

// Row-major 3x3
using Mat3 = std::array<double, 9>;

struct TwoViewCorrespondences {
  std::vector<Vec2> pts1;  // pixel coords
  std::vector<Vec2> pts2;  // pixel coords
};

struct TwoViewCalibCorrespondences {
  std::vector<Vec2> pts1;  // pixel coords
  std::vector<Vec2> pts2;  // pixel coords
  Mat3 K1;                 // intrinsics
  Mat3 K2;
};

// m1
Mat3 EstimateFundamental8Point(const TwoViewCorrespondences& data);
// m2
Mat3 EstimateEssential8Point(const TwoViewCalibCorrespondences& data);

}  // namespace nitr::case002
