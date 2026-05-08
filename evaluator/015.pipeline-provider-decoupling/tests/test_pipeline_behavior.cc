#include "build_pipeline.h"
#include "test_common.h"

int main() {
  nitr::case015::PipelineConfig config;
  config.enable_policy_enrichment = false;

  const auto pipeline = nitr::case015::BuildPipeline(config);
  const auto actual = pipeline.runner.Run(case015_test::SampleEvents());
  const auto expected = case015_test::ReadExpectedLines(
      "evaluator/015.pipeline-provider-decoupling/data/"
      "expected_output_baseline.txt");

  if (actual != expected) {
    return case015_test::Fail("Baseline pipeline output mismatch.");
  }
  return 0;
}
