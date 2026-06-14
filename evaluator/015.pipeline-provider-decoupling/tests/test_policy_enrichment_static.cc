#include "build_pipeline.h"
#include "test_common.h"
#include <gtest/gtest.h>

TEST(Case015PolicyEnrichment, StaticSmoke) {
  nitr::case015::PipelineConfig config;
  config.policy_mode = nitr::case015::PolicyMode::kStatic;
  config.enable_policy_enrichment = true;

  const auto pipeline = nitr::case015::BuildPipeline(config);
  const auto actual = pipeline.runner.Run(case015_test::SampleEvents());
  const auto expected_size = case015_test::SampleEvents().size();
  EXPECT_EQ(actual.size(), expected_size);
}
