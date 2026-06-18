#include <gtest/gtest.h>

#include "build_pipeline.h"
#include "test_common.h"

TEST(Case015PolicyEnrichment, FileSmoke) {
  nitr::case015::PipelineConfig config;
  config.policy_mode = nitr::case015::PolicyMode::kFile;
  config.policy_file_path =
      "evaluator/015.pipeline-provider-decoupling/data/policies.json";
  config.enable_policy_enrichment = true;

  const auto pipeline = nitr::case015::BuildPipeline(config);
  const auto actual = pipeline.runner.Run(case015_test::SampleEvents());
  EXPECT_FALSE(actual.empty());
}
