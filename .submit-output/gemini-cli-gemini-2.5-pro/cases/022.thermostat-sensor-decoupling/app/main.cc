#include "src/thermostat_controller.h"
#include "src/tmp26_sensor.h"
#include <cstdlib>
#include <iostream>

int main(int argc, char* argv[]) {
  if (argc != 2) {
    std::cerr << "Usage: " << argv[0] << " <target_temperature>\n";
    return 1;
  }

  const float target_temperature = std::atof(argv[1]);

  nitr::case022::Tmp26Sensor sensor;
  nitr::case022::ThermostatController controller(target_temperature, &sensor);
  const auto command = controller.Evaluate();

  switch (command) {
    case nitr::case022::ThermostatController::Command::kHeating:
      std::cout << "Heating\n";
      break;
    case nitr::case022::ThermostatController::Command::kCooling:
      std::cout << "Cooling\n";
      break;
    case nitr::case022::ThermostatController::Command::kIdle:
      std::cout << "Idle\n";
      break;
  }

  return 0;
}
