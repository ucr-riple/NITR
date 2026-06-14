#include "execution_plan.h"
#include "pipeline_config.h"
#include <gtest/gtest.h>

using nitr::case016::BuildExecutionPlan;
using nitr::case016::DeviceKind;
using nitr::case016::PipelineConfig;

namespace {

TEST(Case016ExecutionPlan, UnseenConfigPlanShape) {
  const PipelineConfig config = PipelineConfig::FromJsonFile(
      "evaluator/016.device-segment-planner/data/unseen_config.json");
  const auto plan = BuildExecutionPlan(config);

  EXPECT_EQ(3, static_cast<int>(plan.size()));
  EXPECT_EQ(static_cast<int>(DeviceKind::kCpu),
            static_cast<int>(plan[0].device));
  EXPECT_EQ(0, static_cast<int>(plan[0].start_step_index));
  EXPECT_EQ(1, static_cast<int>(plan[0].end_step_index));

  EXPECT_EQ(static_cast<int>(DeviceKind::kGpu),
            static_cast<int>(plan[1].device));
  EXPECT_EQ(2, static_cast<int>(plan[1].start_step_index));
  EXPECT_EQ(3, static_cast<int>(plan[1].end_step_index));

  EXPECT_EQ(static_cast<int>(DeviceKind::kCpu),
            static_cast<int>(plan[2].device));
  EXPECT_EQ(4, static_cast<int>(plan[2].start_step_index));
  EXPECT_EQ(6, static_cast<int>(plan[2].end_step_index));
}
}  // namespace
