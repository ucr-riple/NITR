#include "execution_plan.h"
#include "pipeline_config.h"
#include "test_util.h"

using nitr::case016::BuildExecutionPlan;
using nitr::case016::DeviceKind;
using nitr::case016::PipelineConfig;

namespace {

void TestLegacyExecutionPlan() {
  const PipelineConfig config = PipelineConfig::FromJsonFile(
      "evaluator/016.device-segment-planner/data/legacy_config.json");
  const auto plan = BuildExecutionPlan(config);

  ASSERT_EQ(2, static_cast<int>(plan.size()));
  ASSERT_EQ(static_cast<int>(DeviceKind::kGpu),
            static_cast<int>(plan[0].device));
  ASSERT_EQ(0, static_cast<int>(plan[0].start_step_index));
  ASSERT_EQ(3, static_cast<int>(plan[0].end_step_index));
  ASSERT_EQ(static_cast<int>(DeviceKind::kCpu),
            static_cast<int>(plan[1].device));
  ASSERT_EQ(4, static_cast<int>(plan[1].start_step_index));
  ASSERT_EQ(7, static_cast<int>(plan[1].end_step_index));
}

}  // namespace

int main() {
  return RunTest("execution_plan_legacy", &TestLegacyExecutionPlan);
}
