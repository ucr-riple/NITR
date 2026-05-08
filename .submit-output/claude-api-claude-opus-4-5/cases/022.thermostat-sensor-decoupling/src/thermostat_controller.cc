#include "thermostat_controller.h"

namespace nitr::case022 {

ThermostatController::ThermostatController(float target_temperature)
    : target_temperature_(target_temperature), sensor_(nullptr) {}

ThermostatController::ThermostatController(float target_temperature,
                                           TemperatureSource* sensor)
    : target_temperature_(target_temperature), sensor_(sensor) {}

void ThermostatController::SetTemperatureSource(TemperatureSource* sensor) {
  sensor_ = sensor;
}

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
  float current_temperature = sensor_->ReadTemperature();
  return Evaluate(current_temperature);
}

float ThermostatController::target_temperature() const {
  return target_temperature_;
}

}  // namespace nitr::case022
