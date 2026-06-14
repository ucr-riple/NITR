#include "pipeline_config.h"
#include <gtest/gtest.h>

using nitr::case016::DeviceKind;
using nitr::case016::PipelineConfig;

namespace {

TEST(Case016ConfigLoaderSmoke, LoadsConfigFromJsonText) {
  const std::string json_text = R"JSON(
{
  "legacy_gpu_through_step": 4,
  "steps": [
    {"name": "a"},
    {"name": "b"},
    {"name": "c", "device": "gpu"},
    {"name": "d", "device": "cpu"}
  ]
}
)JSON";

  const PipelineConfig config = PipelineConfig::FromJsonText(json_text);
  EXPECT_EQ(4, static_cast<int>(config.step_count()));
  EXPECT_TRUE(config.legacy_gpu_through_step().has_value());
  EXPECT_EQ(4, config.legacy_gpu_through_step().value());
  EXPECT_TRUE(config.steps()[2].required_device.has_value());
  EXPECT_EQ(static_cast<int>(DeviceKind::kGpu),
            static_cast<int>(config.steps()[2].required_device.value()));
  EXPECT_TRUE(config.steps()[3].required_device.has_value());
  EXPECT_EQ(static_cast<int>(DeviceKind::kCpu),
            static_cast<int>(config.steps()[3].required_device.value()));
}
}  // namespace
