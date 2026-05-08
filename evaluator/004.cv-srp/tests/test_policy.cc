#include <gtest/gtest.h>

#include "policy.h"
#include "types.h"

namespace nitr::case004 {

TEST(Policy, RejectWhenNotEnoughInliers) {
  Metrics m;
  m.num_matches = 100;
  m.num_inliers = 10;
  m.inlier_ratio = 0.10;
  m.median_sampson_error = 0.1;
  EXPECT_EQ(DecideEssential(m), Decision::kReject);
}

TEST(Policy, AcceptWhenPassingThresholds) {
  Metrics m;
  m.num_matches = 100;
  m.num_inliers = 50;
  m.inlier_ratio = 0.50;
  m.median_sampson_error = 0.5;
  EXPECT_EQ(DecideEssential(m), Decision::kAccept);
}

}  // namespace nitr::case004
