### Task

The `ThermostatController` currently requires the current room temperature to be
passed into its evaluation function manually. We need to automate this by
hooking it up to our new hardware sensor.

Update the code so that the thermostat controller can be connected to a temperature source, so callers no longer need to read the sensor and pass the value manually.

### Requirements

- Add a no-argument `Evaluate() const` overload in `ThermostatController`.
- If the current temperature read from the sensor is 2.0 degrees (or more)
  below the target temperature, return `Command::kHeating`.
- If the current temperature read from the sensor is 2.0 degrees (or more)
  above the target temperature, return `Command::kCooling`.
- Otherwise, return `Command::kIdle`.

### Constraints

- Do not add external dependencies.
- Do not modify files under `evaluator/022.thermostat-sensor-decoupling/`.
- You may modify or add new files under `cases/022.thermostat-sensor-decoupling/src/`
  and `cases/022.thermostat-sensor-decoupling/app/`.
- If you modify `src/tmp26_sensor.cc`, preserve the `TMP26_SIMULATOR_TEMP` behavior.
- The project must compile, and all existing tests must pass
  after the change.