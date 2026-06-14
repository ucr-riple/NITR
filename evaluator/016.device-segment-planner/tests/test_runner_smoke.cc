#include "pipeline_config.h"
#include "pipeline_runner.h"
#include <gtest/gtest.h>

using nitr::case016::PipelineConfig;
using nitr::case016::PipelineRunner;

namespace {

TEST(Case016Runner, Smoke) {
  const std::string json_text = R"JSON(
{
  "steps": [
    {"name": "step1"},
    {"name": "step2"},
    {"name": "step3"}
  ]
}
)JSON";

  const PipelineConfig config = PipelineConfig::FromJsonText(json_text);
  const PipelineRunner runner;
  const auto result = runner.Run(config);

  EXPECT_EQ(3, static_cast<int>(result.executed_steps.size()));
  EXPECT_EQ(std::string("step1"), result.executed_steps[0].step_name);
  EXPECT_EQ(std::string("step2"), result.executed_steps[1].step_name);
  EXPECT_EQ(std::string("step3"), result.executed_steps[2].step_name);
}
}  // namespace
