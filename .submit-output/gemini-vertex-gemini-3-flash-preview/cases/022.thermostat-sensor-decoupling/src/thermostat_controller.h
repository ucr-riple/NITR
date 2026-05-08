#pragma once

namespace nitr::case022 {

class TemperatureSource;

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
  Command Evaluate() const;
  float target_temperature() const;

  void ConnectSource(const TemperatureSource* source);

 private:
  float target_temperature_;
  const TemperatureSource* source_ = nullptr;
};

}  // namespace nitr::case022
