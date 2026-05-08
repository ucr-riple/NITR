#include <gtest/gtest.h>

#include "scoring.h"
#include "types.h"

namespace nitr::case004 {

TEST(Scoring, InlierRatioBasic) {
  PairInput in;
  EstimationOutput est;
  est.inliers = {true, false, true, true};  // 3/4

  NormalizedPair norm;
  norm.x0.resize(4);
  norm.x1.resize(4);

  Metrics m = ScoreEssential(in, norm, est);
  EXPECT_EQ(m.num_matches, 4);
  EXPECT_EQ(m.num_inliers, 3);
  EXPECT_NEAR(m.inlier_ratio, 0.75, 1e-12);
}

}  // namespace nitr::case004
