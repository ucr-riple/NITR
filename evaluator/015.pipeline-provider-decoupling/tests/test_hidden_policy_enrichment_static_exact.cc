#include "build_pipeline.h"
#include "test_common.h"
#include <gtest/gtest.h>

TEST(Case015PolicyEnrichment, StaticExactOutput) {
  nitr::case015::PipelineConfig config;
  config.policy_mode = nitr::case015::PolicyMode::kStatic;
  config.enable_policy_enrichment = true;

  const auto pipeline = nitr::case015::BuildPipeline(config);
  const auto actual = pipeline.runner.Run(case015_test::SampleEvents());
  const auto expected = case015_test::ReadExpectedLines(
      "evaluator/015.pipeline-provider-decoupling/data/"
      "expected_output_static.txt");
  EXPECT_EQ(actual, expected);
}
