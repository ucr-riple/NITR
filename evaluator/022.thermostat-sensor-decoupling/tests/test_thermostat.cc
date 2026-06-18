#include <gtest/gtest.h>

#include <string>
#include <type_traits>
#include <utility>
#include <vector>

#include "thermostat_controller.h"

TEST(ThermostatControllerTest, ReturnsConfiguredTargetTemperature) {
  using Controller = nitr::case022::ThermostatController;

  const Controller controller(22.0f);
  EXPECT_FLOAT_EQ(controller.target_temperature(), 22.0f);
}

TEST(ThermostatControllerTest, SupportsNoArgumentEvaluateOverload) {
  using Controller = nitr::case022::ThermostatController;
  static_assert(
      std::is_same_v<decltype(std::declval<const Controller&>().Evaluate()),
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

namespace {

std::string command_to_string(
    const nitr::case022::ThermostatController::Command command) {
  using Command = nitr::case022::ThermostatController::Command;
  switch (command) {
    case Command::kHeating:
      return "Heating";
    case Command::kCooling:
      return "Cooling";
    case Command::kIdle:
      return "Idle";
  }
  return "Unknown";
}

}  // namespace

TEST(ThermostatControllerTest,
     FunctionalBehaviorMatchesApplicationCommandOutputs) {
  using Command = nitr::case022::ThermostatController::Command;
  using Controller = nitr::case022::ThermostatController;

  const std::vector<std::pair<double, Command>> cases = {
      {18.5, Command::kHeating}, {19.0, Command::kHeating},
      {20.0, Command::kHeating}, {20.01, Command::kIdle},
      {22.0, Command::kIdle},    {23.99, Command::kIdle},
      {24.0, Command::kCooling}, {24.5, Command::kCooling},
      {30.0, Command::kCooling},
  };

  for (const auto& [sensor_temp, expected_command] : cases) {
    const float current_temp = static_cast<float>(sensor_temp);
    Controller controller(22.0f);
    const auto command = controller.Evaluate(current_temp);
    EXPECT_EQ(command, expected_command)
        << "current_temp=" << sensor_temp << " expected "
        << command_to_string(expected_command) << ", got "
        << command_to_string(command);
  }
}
