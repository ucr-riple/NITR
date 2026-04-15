#include <gtest/gtest.h>

#include "thermostat_controller.h"

TEST(ThermostatControllerTest, ReturnsConfiguredTargetTemperature) {
  using Controller = nitr::case022::ThermostatController;

  const Controller controller(22.0f);
  EXPECT_FLOAT_EQ(controller.target_temperature(), 22.0f);
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
