#include <cmath>
#include <memory>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "clamp_transform.h"
#include "feature_pipeline.h"
#include "identity_transform.h"
#include "l2_normalize_transform.h"
#include "transform_batch.h"
#include "transform_chain.h"

namespace {

bool NearlyEqual(float a, float b, float eps = 1e-5F) {
  return std::fabs(a - b) <= eps;
}

void ExpectVectorEq(const std::vector<float>& actual,
                    const std::vector<float>& expected,
                    const std::string& prefix) {
  EXPECT_EQ(actual.size(), expected.size()) << prefix << " size mismatch";
  for (std::size_t i = 0; i < expected.size(); ++i) {
    EXPECT_TRUE(NearlyEqual(actual[i], expected[i]))
        << prefix << " value mismatch at index " << i;
  }
}

TEST(Case007MlLspMultistep, PublicClampTransform) {
  nitr::case007::FeaturePipeline pipeline(
      std::make_unique<nitr::case007::ClampTransform>());
  const std::vector<float> input{-2.0F, -0.5F, 0.25F, 3.0F};
  const std::vector<float> expected{-1.0F, -0.5F, 0.25F, 1.0F};
  ExpectVectorEq(pipeline.Run(input), expected, "clamp");
}

TEST(Case007MlLspMultistep, PublicBatchUsesSharedContract) {
  nitr::case007::IdentityTransform transform;
  const std::vector<std::vector<float>> batch{{1.0F, 2.0F}, {}, {-3.0F}};
  const std::vector<std::vector<float>> output =
      nitr::case007::TransformBatch(transform, batch);
  EXPECT_EQ(output.size(), batch.size()) << "batch outer size mismatch";
  for (std::size_t i = 0; i < batch.size(); ++i) {
    ExpectVectorEq(output[i], batch[i], "batch item");
  }
}

TEST(Case007MlLspMultistep, PublicTransformChainAppliesStepsInOrder) {
  nitr::case007::TransformChain chain;
  chain.AddStep(std::make_unique<nitr::case007::ClampTransform>());
  chain.AddStep(std::make_unique<nitr::case007::L2NormalizeTransform>());

  const std::vector<float> input{-3.0F, 4.0F};
  const std::vector<float> output = chain.Transform(input);
  const float inv_norm = 1.0F / std::sqrt(2.0F);
  const std::vector<float> expected{-inv_norm, inv_norm};
  ExpectVectorEq(output, expected, "chain");
}

}  // namespace
