#include <cmath>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include "clamp_transform.h"
#include "feature_pipeline.h"
#include "feature_transform.h"
#include "identity_transform.h"
#include "l2_normalize_transform.h"
#include "transform_batch.h"
#include "transform_chain.h"
#include "transform_factory.h"

namespace {

void Expect(bool condition, const std::string& message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}

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
  Expect(actual.size() == expected.size(), prefix + " size mismatch");
  for (std::size_t i = 0; i < expected.size(); ++i) {
    Expect(NearlyEqual(actual[i], expected[i]), prefix + " value mismatch");
  }
}

void CheckTransformContract(const std::string& name) {
  nitr::case007::FeaturePipeline pipeline(nitr::case007::MakeTransform(name));

  {
    const std::vector<float> input{2.0F, -4.0F, 0.5F};
    const std::vector<float> snapshot = input;
    const std::vector<float> output = pipeline.Run(input);
    Expect(output.size() == input.size(), name + " changed output size");
    Expect(input == snapshot, name + " modified input");
    Expect(IsFiniteVector(output), name + " produced non-finite output");
  }

  {
    const std::vector<float> input;
    const std::vector<float> output = pipeline.Run(input);
    Expect(output.empty(), name + " failed on empty input");
  }
}

void CheckL2ZeroVectorIsSafe() {
  nitr::case007::FeaturePipeline pipeline(
      std::make_unique<nitr::case007::L2NormalizeTransform>());
  const std::vector<float> input{0.0F, 0.0F, 0.0F};
  const std::vector<float> output = pipeline.Run(input);
  Expect(output.size() == input.size(), "l2 zero vector changed size");
  Expect(IsFiniteVector(output), "l2 zero vector produced NaN or Inf");
  for (float value : output) {
    Expect(value == 0.0F, "l2 zero vector should remain zero");
  }
}

void CheckL2UnitNormOnNonZeroInput() {
  nitr::case007::FeaturePipeline pipeline(
      std::make_unique<nitr::case007::L2NormalizeTransform>());
  const std::vector<float> input{1.0F, 2.0F, 2.0F};
  const std::vector<float> output = pipeline.Run(input);
  Expect(std::fabs(Norm(output) - 1.0F) <= 1e-5F, "l2 output is not unit norm");
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
  Expect(output.size() == batch.size(), "batch outer size mismatch");
  ExpectVectorEq(output[0], std::vector<float>({-1.0F, 0.5F, 1.0F}),
                 "batch clamp first");
  Expect(output[1].empty(), "batch clamp empty mismatch");
  ExpectVectorEq(output[2], std::vector<float>({1.0F}), "batch clamp third");
}

void CheckBatchPathForL2() {
  nitr::case007::L2NormalizeTransform transform;
  const std::vector<std::vector<float>> batch{
      {3.0F, 4.0F}, {0.0F, 0.0F}, {1.0F}};
  const std::vector<std::vector<float>> output =
      nitr::case007::TransformBatch(transform, batch);
  Expect(output.size() == batch.size(), "l2 batch outer size mismatch");
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

}  // namespace

int main() {
  try {
    CheckTransformContract("identity");
    CheckTransformContract("l2");
    CheckClampExistsAndClamps();
    CheckTransformContract("clamp");
    CheckL2ZeroVectorIsSafe();
    CheckL2UnitNormOnNonZeroInput();
    CheckBatchPathForClamp();
    CheckBatchPathForL2();
    CheckTransformChainWithSingleStep();
    CheckTransformChainOrder();
    CheckTransformChainWorksAsFeatureTransform();
  } catch (const std::exception& ex) {
    std::cerr << "HIDDEN TEST FAILURE: " << ex.what() << '\n';
    return 1;
  }
  std::cout << "hidden tests passed\n";
  return 0;
}
