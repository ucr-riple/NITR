#pragma once

namespace nitr::case022 {

class TemperatureSource {
 public:
  virtual ~TemperatureSource() = default;
  virtual float ReadTemperature() const = 0;
};

}  // namespace nitr::case022
