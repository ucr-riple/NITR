#include "thermostat_controller.h"
#include "tmp26_sensor.h"

int main() {
  nitr::case022::Tmp26Sensor sensor;
  nitr::case022::ThermostatController controller(22.0f);
  controller.ConnectSource(&sensor);

  // The controller can now be evaluated without passing a temperature manually.
  [[maybe_unused]] auto command = controller.Evaluate();

  return 0;
}
