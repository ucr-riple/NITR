#include <gtest/gtest.h>

#include "pipeline.h"
#include "types.h"

namespace nitr::case004 {

static PairInput MakeMinimalInput(int num_matches) {
  PairInput in;
  in.cam = {525, 525, 319.5, 239.5};
  in.f0.keypoints_px.resize(num_matches);
  in.f1.keypoints_px.resize(num_matches);
  in.matches.reserve(num_matches);
  for (int i = 0; i < num_matches; ++i) {
    in.f0.keypoints_px[i] = {double(i), double(i)};
    in.f1.keypoints_px[i] = {double(i), double(i)};
    in.matches.push_back({i, i});
  }
  in.opt.model = "E";
  in.opt.ransac_thresh_px = 1.0;
  in.opt.max_iters = 100;
  return in;
}

TEST(Pipeline, EstimationFailedIfTooFewMatches) {
  PairInput in = MakeMinimalInput(7);
  RunOutput out = RunPipeline(in);
  EXPECT_EQ(out.code, ErrorCode::kEstimationFailed);
}

}  // namespace nitr::case004
