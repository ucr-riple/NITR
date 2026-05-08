#include "thermostat_controller.h"
#include "temperature_source.h"

namespace nitr::case022 {

ThermostatController::ThermostatController(float target_temperature)
    : target_temperature_(target_temperature), source_(nullptr) {}

void ThermostatController::ConnectSource(const TemperatureSource* source) {
  source_ = source;
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
  if (source_) {
    return Evaluate(source_->ReadTemperature());
  }
  return Command::kIdle;
}

float ThermostatController::target_temperature() const {
  return target_temperature_;
}

}  // namespace nitr::case022
