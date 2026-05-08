#include "thermostat_controller.h"

namespace nitr::case022 {

ThermostatController::ThermostatController(float target_temperature)
    : target_temperature_(target_temperature), sensor_(nullptr) {}

ThermostatController::ThermostatController(float target_temperature, TemperatureSensor* sensor)
    : target_temperature_(target_temperature), sensor_(sensor) {}

void ThermostatController::set_sensor(TemperatureSensor* sensor) {
  sensor_ = sensor;
}

ThermostatController::Command ThermostatController::Evaluate(float current_temperature) const {
  if (current_temperature <= target_temperature_ - kTemperatureDeltaThreshold) {
    return Command::kHeating;
  }
  if (current_temperature >= target_temperature_ + kTemperatureDeltaThreshold) {
    return Command::kCooling;
  }
  return Command::kIdle;
}

ThermostatController::Command ThermostatController::Evaluate() const {
  if (sensor_) {
    return Evaluate(sensor_->ReadTemperature());
  }
  return Command::kIdle;
}

float ThermostatController::target_temperature() const {
  return target_temperature_;
}

}  // namespace nitr::case022
