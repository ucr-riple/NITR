#include <gtest/gtest.h>

#include <vector>

#include "build_pipeline.h"
#include "test_common.h"

namespace {

std::vector<nitr::case015::Event> PartnerAndFallbackEvents() {
  return {
      {"partner", "export ready", 5},
      {"unknown", "manual review", 3},
  };
}

std::vector<std::string> ExpectedStatic() {
  return {
      "source=partner;payload=EXPORT_READY;score=5;policy_tier=archive;"
      "retention_days=180",
      "source=unknown;payload=MANUAL_REVIEW;score=3;policy_tier=standard;"
      "retention_days=30",
  };
}

std::vector<std::string> ExpectedFile() {
  return {
      "source=partner;payload=EXPORT_READY;score=5;policy_tier=archive;"
      "retention_days=365",
      "source=unknown;payload=MANUAL_REVIEW;score=3;policy_tier=standard;"
      "retention_days=30",
  };
}

}  // namespace

TEST(Case015PolicyEnrichment, FallbackAndPartnerBehavior) {
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

  const auto static_actual =
      static_pipeline.runner.Run(PartnerAndFallbackEvents());
  const auto file_actual = file_pipeline.runner.Run(PartnerAndFallbackEvents());
  EXPECT_EQ(static_actual, ExpectedStatic());
  EXPECT_EQ(file_actual, ExpectedFile());
  EXPECT_NE(static_actual, file_actual);
}
