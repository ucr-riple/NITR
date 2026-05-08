#include "tmp26_sensor.h"
#include <cstdlib>

namespace nitr::case022 {

float Tmp26Sensor::ReadTemperature() const {
  const char* env_temp = std::getenv("TMP26_SIMULATOR_TEMP");
  if (env_temp != nullptr) {
    return static_cast<float>(std::atof(env_temp));
  }
  return 20.0f;
}

}  // namespace nitr::case022
