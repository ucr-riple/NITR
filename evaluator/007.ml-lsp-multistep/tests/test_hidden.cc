#include <cmath>
#include <limits>
#include <memory>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "clamp_transform.h"
#include "feature_pipeline.h"
#include "feature_transform.h"
#include "identity_transform.h"
#include "l2_normalize_transform.h"
#include "transform_batch.h"
#include "transform_chain.h"
#include "transform_factory.h"

namespace {

bool NearlyEqual(float a, float b, float eps = 1e-5F) {
  return std::fabs(a - b) <= eps;
}

bool IsFiniteVector(const std::vector<float>& values) {
  for (float value : values) {
    if (!std::isfinite(value)) {
      return false;
    }
  }
  return true;
}

float Norm(const std::vector<float>& values) {
  float squared_sum = 0.0F;
  for (float value : values) {
    squared_sum += value * value;
  }
  return std::sqrt(squared_sum);
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

void CheckTransformContract(const std::string& name) {
  nitr::case007::FeaturePipeline pipeline(nitr::case007::MakeTransform(name));

  {
    const std::vector<float> input{2.0F, -4.0F, 0.5F};
    const std::vector<float> snapshot = input;
    const std::vector<float> output = pipeline.Run(input);
    EXPECT_EQ(output.size(), input.size()) << name << " changed output size";
    EXPECT_EQ(input, snapshot) << name << " modified input";
    EXPECT_TRUE(IsFiniteVector(output)) << name << " produced non-finite output";
  }

  {
    const std::vector<float> input;
    const std::vector<float> output = pipeline.Run(input);
    EXPECT_TRUE(output.empty()) << name << " failed on empty input";
  }
}

void CheckL2ZeroVectorIsSafe() {
  nitr::case007::FeaturePipeline pipeline(
      std::make_unique<nitr::case007::L2NormalizeTransform>());
  const std::vector<float> input{0.0F, 0.0F, 0.0F};
  const std::vector<float> output = pipeline.Run(input);
  EXPECT_EQ(output.size(), input.size()) << "l2 zero vector changed size";
  EXPECT_TRUE(IsFiniteVector(output)) << "l2 zero vector produced NaN or Inf";
  for (float value : output) {
    EXPECT_EQ(value, 0.0F) << "l2 zero vector should remain zero";
  }
}

void CheckL2UnitNormOnNonZeroInput() {
  nitr::case007::FeaturePipeline pipeline(
      std::make_unique<nitr::case007::L2NormalizeTransform>());
  const std::vector<float> input{1.0F, 2.0F, 2.0F};
  const std::vector<float> output = pipeline.Run(input);
  EXPECT_TRUE(std::fabs(Norm(output) - 1.0F) <= 1e-5F)
      << "l2 output is not unit norm";
}

void CheckClampExistsAndClamps() {
  nitr::case007::FeaturePipeline pipeline(
      nitr::case007::MakeTransform("clamp"));
  const std::vector<float> input{-2.0F, -1.0F, -0.25F, 0.25F, 1.0F, 2.0F};
  const std::vector<float> expected{-1.0F, -1.0F, -0.25F, 0.25F, 1.0F, 1.0F};
  ExpectVectorEq(pipeline.Run(input), expected, "clamp");
}

void CheckBatchPathForClamp() {
  nitr::case007::ClampTransform transform;
  const std::vector<std::vector<float>> batch{{-3.0F, 0.5F, 2.0F}, {}, {1.0F}};
  const std::vector<std::vector<float>> output =
      nitr::case007::TransformBatch(transform, batch);
  EXPECT_EQ(output.size(), batch.size()) << "batch outer size mismatch";
  ExpectVectorEq(output[0], std::vector<float>({-1.0F, 0.5F, 1.0F}),
                 "batch clamp first");
  EXPECT_TRUE(output[1].empty()) << "batch clamp empty mismatch";
  ExpectVectorEq(output[2], std::vector<float>({1.0F}), "batch clamp third");
}

void CheckBatchPathForL2() {
  nitr::case007::L2NormalizeTransform transform;
  const std::vector<std::vector<float>> batch{
      {3.0F, 4.0F}, {0.0F, 0.0F}, {1.0F}};
  const std::vector<std::vector<float>> output =
      nitr::case007::TransformBatch(transform, batch);
  EXPECT_EQ(output.size(), batch.size()) << "l2 batch outer size mismatch";
  ExpectVectorEq(output[0], std::vector<float>({0.6F, 0.8F}), "l2 batch first");
  ExpectVectorEq(output[1], std::vector<float>({0.0F, 0.0F}),
                 "l2 batch second");
  ExpectVectorEq(output[2], std::vector<float>({1.0F}), "l2 batch third");
}

void CheckTransformChainWithSingleStep() {
  nitr::case007::TransformChain chain;
  chain.AddStep(std::make_unique<nitr::case007::ClampTransform>());
  const std::vector<float> input{-3.0F, 0.2F, 5.0F};
  ExpectVectorEq(chain.Transform(input),
                 std::vector<float>({-1.0F, 0.2F, 1.0F}), "chain single step");
}

void CheckTransformChainOrder() {
  nitr::case007::TransformChain chain;
  chain.AddStep(std::make_unique<nitr::case007::ClampTransform>());
  chain.AddStep(std::make_unique<nitr::case007::L2NormalizeTransform>());
  const float inv_norm = 1.0F / std::sqrt(2.0F);
  ExpectVectorEq(chain.Transform(std::vector<float>({-3.0F, 4.0F})),
                 std::vector<float>({-inv_norm, inv_norm}), "chain order");
}

void CheckTransformChainWorksAsFeatureTransform() {
  auto chain = std::make_unique<nitr::case007::TransformChain>();
  chain->AddStep(std::make_unique<nitr::case007::ClampTransform>());
  chain->AddStep(std::make_unique<nitr::case007::IdentityTransform>());
  nitr::case007::FeaturePipeline pipeline(std::move(chain));
  ExpectVectorEq(pipeline.Run(std::vector<float>({-2.0F, 3.0F})),
                 std::vector<float>({-1.0F, 1.0F}), "chain as transform");
}

TEST(Case007MlLspMultistep, HiddenContractForIdentityTransform) {
  CheckTransformContract("identity");
}

TEST(Case007MlLspMultistep, HiddenContractForL2Transform) {
  CheckTransformContract("l2");
}

TEST(Case007MlLspMultistep, HiddenClampLimitsAndPreservesInput) {
  CheckClampExistsAndClamps();
}

TEST(Case007MlLspMultistep, HiddenContractForClampTransform) {
  CheckTransformContract("clamp");
}

TEST(Case007MlLspMultistep, HiddenL2ZeroVectorIsSafe) {
  CheckL2ZeroVectorIsSafe();
}

TEST(Case007MlLspMultistep, HiddenL2OutputHasUnitNormOnNonZeroInput) {
  CheckL2UnitNormOnNonZeroInput();
}

TEST(Case007MlLspMultistep, HiddenBatchClampPath) {
  CheckBatchPathForClamp();
}

TEST(Case007MlLspMultistep, HiddenBatchL2Path) {
  CheckBatchPathForL2();
}

TEST(Case007MlLspMultistep, HiddenChainSingleStep) {
  CheckTransformChainWithSingleStep();
}

TEST(Case007MlLspMultistep, HiddenChainOrder) {
  CheckTransformChainOrder();
}

TEST(Case007MlLspMultistep, HiddenChainAsFeatureTransform) {
  CheckTransformChainWorksAsFeatureTransform();
}

}  // namespace
