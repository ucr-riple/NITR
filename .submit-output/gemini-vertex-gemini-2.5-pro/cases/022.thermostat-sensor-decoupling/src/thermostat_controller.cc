#include "src/thermostat_controller.h"

#include "src/tmp26_sensor.h"

namespace nitr::case022 {

ThermostatController::ThermostatController(float target_temperature)
    : target_temperature_(target_temperature) {}

ThermostatController::Command ThermostatController::Evaluate(
    float current_temperature) const {
  if (current_temperature <= target_temperature_ - kTemperatureDeltaThreshold) {
    return Command::kHeating;
  }
  if (current_temperature >= target_temperature_ + kTemperatureDeltaThreshold) {
    return Command::kCooling;
  }
  return Command::kIdle;
}

ThermostatController::Command ThermostatController::Evaluate() const {
  const Tmp26Sensor sensor;
  const float current_temperature = sensor.ReadTemperature();
  return Evaluate(current_temperature);
}

float ThermostatController::target_temperature() const {
  return target_temperature_;
}

}  // namespace nitr::case022
