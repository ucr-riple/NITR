#include "tmp26_sensor.h"

#include <cstdlib>
#include <string>

namespace nitr::case022 {

float Tmp26Sensor::ReadTemperature() const {
  if (const char* env_temp = std::getenv("TMP26_SIMULATOR_TEMP")) {
    return std::stof(env_temp);
  }
  return 22.5f;
}

}  // namespace nitr::case022
