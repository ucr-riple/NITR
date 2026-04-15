#pragma once

namespace nitr::case022 {

class ThermostatController {
 public:
  static constexpr float kTemperatureDeltaThreshold = 2.0f;

  enum class Command {
    kHeating,
    kCooling,
    kIdle,
  };

  explicit ThermostatController(float target_temperature);

  Command Evaluate(float current_temperature) const;
  float target_temperature() const;

 private:
  float target_temperature_;
};

}
