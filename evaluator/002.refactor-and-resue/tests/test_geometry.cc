#include <gtest/gtest.h>

#include <Eigen/Dense>
#include <cmath>
#include <vector>

#include "geometry.h"

namespace nitr::case002 {
namespace {

struct Vec3 {
  double x;
  double y;
  double z;
};

Mat3 MakeIntrinsics(double fx, double fy, double cx, double cy) {
  return Mat3{
      fx, 0.0, cx, 0.0, fy, cy, 0.0, 0.0, 1.0,
  };
}

Vec2 ProjectPointIdentity(const Vec3& point) {
  return Vec2{point.x / point.z, point.y / point.z};
}

Vec2 ProjectPointTranslated(const Vec3& point, double tx, double ty,
                            double tz) {
  const double x = point.x + tx;
  const double y = point.y + ty;
  const double z = point.z + tz;
  return Vec2{x / z, y / z};
}

Vec2 ApplyIntrinsics(const Vec2& normalized, const Mat3& k) {
  return Vec2{
      k[0] * normalized.x + k[2],
      k[4] * normalized.y + k[5],
  };
}

double FundamentalResidual(const Mat3& f, const Vec2& p1, const Vec2& p2) {
  const double x1[3] = {p1.x, p1.y, 1.0};
  const double x2[3] = {p2.x, p2.y, 1.0};

  const double fx1[3] = {
      f[0] * x1[0] + f[1] * x1[1] + f[2] * x1[2],
      f[3] * x1[0] + f[4] * x1[1] + f[5] * x1[2],
      f[6] * x1[0] + f[7] * x1[1] + f[8] * x1[2],
  };
  return std::abs(x2[0] * fx1[0] + x2[1] * fx1[1] + x2[2] * fx1[2]);
}

double EssentialResidual(const Mat3& e, const Vec2& p1, const Vec2& p2,
                         const Mat3& k1, const Mat3& k2) {
  const double x1[3] = {
      (p1.x - k1[2]) / k1[0],
      (p1.y - k1[5]) / k1[4],
      1.0,
  };
  const double x2[3] = {
      (p2.x - k2[2]) / k2[0],
      (p2.y - k2[5]) / k2[4],
      1.0,
  };

  const double ex1[3] = {
      e[0] * x1[0] + e[1] * x1[1] + e[2] * x1[2],
      e[3] * x1[0] + e[4] * x1[1] + e[5] * x1[2],
      e[6] * x1[0] + e[7] * x1[1] + e[8] * x1[2],
  };
  return std::abs(x2[0] * ex1[0] + x2[1] * ex1[1] + x2[2] * ex1[2]);
}

double Mean(const std::vector<double>& values) {
  double sum = 0.0;
  for (double value : values) {
    sum += value;
  }
  return values.empty() ? 0.0 : sum / static_cast<double>(values.size());
}

Eigen::Matrix3d ToEigen(const Mat3& m) {
  Eigen::Matrix3d out;
  out << m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8];
  return out;
}

std::vector<Vec3> SyntheticPoints() {
  return {
      {-1.2, -0.4, 4.0}, {-0.8, 0.7, 4.4}, {-0.1, -0.6, 5.1}, {0.3, 0.5, 5.6},
      {0.8, -0.2, 6.0},  {1.0, 0.9, 6.8},  {-0.5, 1.1, 5.3},  {0.6, -1.0, 4.7},
      {1.3, 0.2, 7.2},   {-1.1, 0.4, 6.1},
  };
}

}  // namespace

TEST(GeometryTests, FundamentalEstimateProducesLowEpipolarResidual) {
  const std::vector<Vec3> points = SyntheticPoints();
  constexpr double tx = 0.35;
  constexpr double ty = -0.08;
  constexpr double tz = 0.18;

  TwoViewCorrespondences data;
  for (const Vec3& point : points) {
    data.pts1.push_back(ProjectPointIdentity(point));
    data.pts2.push_back(ProjectPointTranslated(point, tx, ty, tz));
  }

  const Mat3 f = EstimateFundamental8Point(data);

  std::vector<double> residuals;
  residuals.reserve(points.size());
  for (size_t i = 0; i < points.size(); ++i) {
    residuals.push_back(FundamentalResidual(f, data.pts1[i], data.pts2[i]));
  }

  EXPECT_LT(Mean(residuals), 1e-3);
}

TEST(GeometryTests, EssentialEstimateProducesLowNormalizedResidual) {
  const std::vector<Vec3> points = SyntheticPoints();
  constexpr double tx = 0.28;
  constexpr double ty = 0.04;
  constexpr double tz = 0.12;

  const Mat3 k1 = MakeIntrinsics(700.0, 710.0, 320.0, 240.0);
  const Mat3 k2 = MakeIntrinsics(730.0, 725.0, 300.0, 210.0);

  TwoViewCalibCorrespondences data;
  data.K1 = k1;
  data.K2 = k2;

  for (const Vec3& point : points) {
    const Vec2 p1_norm = ProjectPointIdentity(point);
    const Vec2 p2_norm = ProjectPointTranslated(point, tx, ty, tz);
    data.pts1.push_back(ApplyIntrinsics(p1_norm, k1));
    data.pts2.push_back(ApplyIntrinsics(p2_norm, k2));
  }

  const Mat3 e = EstimateEssential8Point(data);

  std::vector<double> residuals;
  residuals.reserve(points.size());
  for (size_t i = 0; i < points.size(); ++i) {
    residuals.push_back(
        EssentialResidual(e, data.pts1[i], data.pts2[i], k1, k2));
  }

  EXPECT_LT(Mean(residuals), 1e-3);

  const Eigen::JacobiSVD<Eigen::Matrix3d> svd(
      ToEigen(e), Eigen::ComputeFullU | Eigen::ComputeFullV);
  const Eigen::Vector3d singular_values = svd.singularValues();
  EXPECT_GT(singular_values(0), 1e-6);
  EXPECT_GT(singular_values(1), 1e-6);
  EXPECT_NEAR(singular_values(0), singular_values(1), 1e-3);
  EXPECT_NEAR(singular_values(2), 0.0, 1e-6);
}

}  // namespace nitr::case002
