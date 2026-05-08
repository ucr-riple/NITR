#include "build_pipeline.h"
#include "test_common.h"

int main() {
  nitr::case015::PipelineConfig config;
  config.policy_mode = nitr::case015::PolicyMode::kFile;
  config.policy_file_path =
      "evaluator/015.pipeline-provider-decoupling/data/policies.json";
  config.enable_policy_enrichment = true;

  const auto pipeline = nitr::case015::BuildPipeline(config);
  const auto actual = pipeline.runner.Run(case015_test::SampleEvents());
  const auto expected = case015_test::ReadExpectedLines(
      "evaluator/015.pipeline-provider-decoupling/data/"
      "expected_output_file.txt");

  if (actual != expected) {
    return case015_test::Fail("File-mode exact output mismatch.");
  }
  return 0;
}
