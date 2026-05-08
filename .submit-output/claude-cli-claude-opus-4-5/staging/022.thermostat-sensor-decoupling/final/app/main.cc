#include <iostream>
#include <string>

#include "thermostat_controller.h"
#include "tmp26_sensor.h"

namespace {

const char* toString(nitr::case022::ThermostatController::Command command) {
  using Command = nitr::case022::ThermostatController::Command;
  switch (command) {
    case Command::kHeating:
      return "Heating";
    case Command::kCooling:
      return "Cooling";
    case Command::kIdle:
      return "Idle";
  }
  return "Unknown";
}

}

int main(int argc, char** argv) {
  if (argc < 2) {
    std::cerr << "Usage: " << argv[0] << " <target_temperature>\n";
    return 1;
  }
  float target = std::stof(argv[1]);

  nitr::case022::ThermostatController controller(target);

  nitr::case022::Tmp26Sensor sensor;
  const float current_temp = sensor.ReadTemperature();
  const auto command = controller.Evaluate(current_temp);

  std::cout << toString(command) << '\n';
  return 0;
}
