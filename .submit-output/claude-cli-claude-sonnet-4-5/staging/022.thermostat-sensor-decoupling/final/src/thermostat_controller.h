#pragma once

namespace nitr::case022 {

class Tmp26Sensor;

class ThermostatController {
 public:
  static constexpr float kTemperatureDeltaThreshold = 2.0f;

  enum class Command {
    kHeating,
    kCooling,
    kIdle,
  };

  explicit ThermostatController(float target_temperature);

  void ConnectSensor(const Tmp26Sensor* sensor);
  Command Evaluate(float current_temperature) const;
  Command Evaluate() const;
  float target_temperature() const;

 private:
  float target_temperature_;
  const Tmp26Sensor* sensor_ = nullptr;
};

}  // namespace nitr::case022
