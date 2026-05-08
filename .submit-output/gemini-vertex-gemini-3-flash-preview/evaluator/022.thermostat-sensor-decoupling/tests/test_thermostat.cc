#include <gtest/gtest.h>

#include <cstdlib>
#include <type_traits>

#include "thermostat_controller.h"

TEST(ThermostatControllerTest, ReturnsConfiguredTargetTemperature) {
  using Controller = nitr::case022::ThermostatController;

  const Controller controller(22.0f);
  EXPECT_FLOAT_EQ(controller.target_temperature(), 22.0f);
}

TEST(ThermostatControllerTest, SupportsNoArgumentEvaluateOverload) {
  using Controller = nitr::case022::ThermostatController;
  static_assert(std::is_same_v<decltype(std::declval<const Controller&>().Evaluate()),
                               Controller::Command>);
}

TEST(ThermostatControllerTest, HeatsAtOrBelowLowerThreshold) {
  using Controller = nitr::case022::ThermostatController;

  const Controller controller(22.0f);
  EXPECT_EQ(controller.Evaluate(20.0f), Controller::Command::kHeating);
  EXPECT_EQ(controller.Evaluate(19.9f), Controller::Command::kHeating);
}

TEST(ThermostatControllerTest, CoolsAtOrAboveUpperThreshold) {
  using Controller = nitr::case022::ThermostatController;

  const Controller controller(22.0f);
  EXPECT_EQ(controller.Evaluate(24.0f), Controller::Command::kCooling);
  EXPECT_EQ(controller.Evaluate(24.1f), Controller::Command::kCooling);
}

TEST(ThermostatControllerTest, IdlesInsideThresholdBand) {
  using Controller = nitr::case022::ThermostatController;

  const Controller controller(22.0f);
  EXPECT_EQ(controller.Evaluate(22.0f), Controller::Command::kIdle);
  EXPECT_EQ(controller.Evaluate(20.1f), Controller::Command::kIdle);
  EXPECT_EQ(controller.Evaluate(23.9f), Controller::Command::kIdle);
}

TEST(ThermostatControllerTest, NoArgumentEvaluateHeatsAtOrBelowLowerThreshold) {
  using Controller = nitr::case022::ThermostatController;

  unsetenv("TMP26_SIMULATOR_TEMP");
  const Controller controller(22.0f);

  ASSERT_EQ(setenv("TMP26_SIMULATOR_TEMP", "20.0", 1), 0);
  EXPECT_EQ(controller.Evaluate(), Controller::Command::kHeating);
  ASSERT_EQ(setenv("TMP26_SIMULATOR_TEMP", "19.9", 1), 0);
  EXPECT_EQ(controller.Evaluate(), Controller::Command::kHeating);

  unsetenv("TMP26_SIMULATOR_TEMP");
}

TEST(ThermostatControllerTest, NoArgumentEvaluateCoolsAtOrAboveUpperThreshold) {
  using Controller = nitr::case022::ThermostatController;

  unsetenv("TMP26_SIMULATOR_TEMP");
  const Controller controller(22.0f);

  ASSERT_EQ(setenv("TMP26_SIMULATOR_TEMP", "24.0", 1), 0);
  EXPECT_EQ(controller.Evaluate(), Controller::Command::kCooling);
  ASSERT_EQ(setenv("TMP26_SIMULATOR_TEMP", "24.1", 1), 0);
  EXPECT_EQ(controller.Evaluate(), Controller::Command::kCooling);

  unsetenv("TMP26_SIMULATOR_TEMP");
}

TEST(ThermostatControllerTest, NoArgumentEvaluateIdlesInsideThresholdBand) {
  using Controller = nitr::case022::ThermostatController;

  unsetenv("TMP26_SIMULATOR_TEMP");
  const Controller controller(22.0f);

  ASSERT_EQ(setenv("TMP26_SIMULATOR_TEMP", "22.0", 1), 0);
  EXPECT_EQ(controller.Evaluate(), Controller::Command::kIdle);
  ASSERT_EQ(setenv("TMP26_SIMULATOR_TEMP", "20.1", 1), 0);
  EXPECT_EQ(controller.Evaluate(), Controller::Command::kIdle);
  ASSERT_EQ(setenv("TMP26_SIMULATOR_TEMP", "23.9", 1), 0);
  EXPECT_EQ(controller.Evaluate(), Controller::Command::kIdle);

  unsetenv("TMP26_SIMULATOR_TEMP");
}
