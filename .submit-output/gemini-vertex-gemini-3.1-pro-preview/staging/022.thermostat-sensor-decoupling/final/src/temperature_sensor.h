#pragma once

namespace nitr::case022 {

class TemperatureSensor {
 public:
  virtual ~TemperatureSensor() = default;
  virtual float ReadTemperature() const = 0;
};

}  // namespace nitr::case022
