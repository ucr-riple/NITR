#include "build_pipeline.h"
#include "test_common.h"

int main() {
  nitr::case015::PipelineConfig config;
  config.policy_mode = nitr::case015::PolicyMode::kStatic;
  config.enable_policy_enrichment = true;

  const auto pipeline = nitr::case015::BuildPipeline(config);
  const auto actual = pipeline.runner.Run(case015_test::SampleEvents());

  if (actual.size() != case015_test::SampleEvents().size()) {
    return case015_test::Fail(
        "Static-mode smoke test failed: output size mismatch.");
  }
  return 0;
}
