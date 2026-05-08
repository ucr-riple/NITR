#include "thermostat_controller.h"

#include "temperature_source.h"

namespace nitr::case022 {

ThermostatController::ThermostatController(float target_temperature)
    : target_temperature_(target_temperature), sensor_(nullptr) {}

void ThermostatController::ConnectSensor(TemperatureSource* source) {
  sensor_ = source;
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
  return Evaluate(sensor_->ReadTemperature());
}

float ThermostatController::target_temperature() const {
  return target_temperature_;
}

}  // namespace nitr::case022
