#include "build_pipeline.h"
#include "test_common.h"
#include <gtest/gtest.h>

TEST(Case015PolicyEnrichment, ProviderSwitching) {
  nitr::case015::PipelineConfig static_config;
  static_config.policy_mode = nitr::case015::PolicyMode::kStatic;
  static_config.enable_policy_enrichment = true;

  nitr::case015::PipelineConfig file_config;
  file_config.policy_mode = nitr::case015::PolicyMode::kFile;
  file_config.policy_file_path =
      "evaluator/015.pipeline-provider-decoupling/data/policies.json";
  file_config.enable_policy_enrichment = true;

  const auto static_pipeline = nitr::case015::BuildPipeline(static_config);
  const auto file_pipeline = nitr::case015::BuildPipeline(file_config);

  const auto static_output =
      static_pipeline.runner.Run(case015_test::SampleEvents());
  const auto file_output =
      file_pipeline.runner.Run(case015_test::SampleEvents());
  EXPECT_NE(static_output, file_output);
}
