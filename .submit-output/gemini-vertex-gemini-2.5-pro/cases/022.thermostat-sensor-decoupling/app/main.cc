#include <iostream>

#include "src/thermostat_controller.h"

int main() {
  // Create a thermostat controller with a target temperature of 25.0 C.
  nitr::case022::ThermostatController controller(25.0f);

  // The controller now reads from the sensor internally.
  // The Tmp26Sensor might be compiled with a simulated temperature,
  // so the output could vary based on build flags.
  const auto command = controller.Evaluate();

  std::cout << "Target: " << controller.target_temperature() << " C\n";
  std::cout << "Command: ";
  switch (command) {
    case nitr::case022::ThermostatController::Command::kHeating:
      std::cout << "Heating";
      break;
    case nitr::case022::ThermostatController::Command::kCooling:
      std::cout << "Cooling";
      break;
    case nitr::case022::ThermostatController::Command::kIdle:
      std::cout << "Idle";
      break;
  }
  std::cout << std::endl;

  return 0;
}
