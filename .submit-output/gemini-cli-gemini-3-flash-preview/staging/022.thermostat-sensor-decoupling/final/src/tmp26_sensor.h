#pragma once

#include "temperature_source.h"

namespace nitr::case022 {

class Tmp26Sensor : public TemperatureSource {
 public:
  float ReadTemperature() const override;
};

}  // namespace nitr::case022
