#include <gtest/gtest.h>

#include <vector>

#include "pipeline_config.h"
#include "pipeline_runner.h"

using nitr::case016::DeviceKind;
using nitr::case016::PipelineConfig;
using nitr::case016::PipelineRunner;

namespace {

TEST(Case016Runner, RespectsSegmentation) {
  const PipelineConfig config = PipelineConfig::FromJsonFile(
      "evaluator/016.device-segment-planner/data/updated_config.json");
  const PipelineRunner runner;
  const auto result = runner.Run(config);

  EXPECT_EQ(8, static_cast<int>(result.executed_steps.size()));
  const std::vector<DeviceKind> expected_devices = {
      DeviceKind::kGpu, DeviceKind::kGpu, DeviceKind::kGpu, DeviceKind::kGpu,
      DeviceKind::kCpu, DeviceKind::kGpu, DeviceKind::kCpu, DeviceKind::kCpu,
  };

  for (std::size_t i = 0; i < expected_devices.size(); ++i) {
    EXPECT_EQ(static_cast<int>(expected_devices[i]),
              static_cast<int>(result.executed_steps[i].device));
  }
}
}  // namespace
