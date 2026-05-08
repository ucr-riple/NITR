#include "thermostat_controller.h"

#include "temperature_source.h"
#include "tmp26_sensor.h"

namespace nitr::case022 {

namespace {

const TemperatureSource& GetDefaultSensor() {
  static Tmp26Sensor default_sensor;
  return default_sensor;
}

}  // namespace

ThermostatController::ThermostatController(float target_temperature)
    : target_temperature_(target_temperature), source_(&GetDefaultSensor()) {}

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
  return Evaluate(source_->ReadTemperature());
}

float ThermostatController::target_temperature() const {
  return target_temperature_;
}

void ThermostatController::Connect(const TemperatureSource& source) {
  source_ = &source;
}

}  // namespace nitr::case022
