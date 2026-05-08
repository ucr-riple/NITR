#pragma once

#include "temperature_sensor.h"

namespace nitr::case022 {

class Tmp26Sensor : public TemperatureSensor {
 public:
  float ReadTemperature() const override;
};

}  // namespace nitr::case022
