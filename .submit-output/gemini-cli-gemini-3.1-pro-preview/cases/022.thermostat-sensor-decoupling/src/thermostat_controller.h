#pragma once

#include "temperature_sensor.h"

namespace nitr::case022 {

class ThermostatController {
 public:
  static constexpr float kTemperatureDeltaThreshold = 2.0f;

  enum class Command {
    kHeating,
    kCooling,
    kIdle,
  };

  explicit ThermostatController(float target_temperature, const TemperatureSensor* sensor = nullptr);

  Command Evaluate(float current_temperature) const;
  Command Evaluate() const;
  float target_temperature() const;

 private:
  float target_temperature_;
  const TemperatureSensor* sensor_;
};

}  // namespace nitr::case022
