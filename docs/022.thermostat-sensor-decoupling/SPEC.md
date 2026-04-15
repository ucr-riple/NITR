---
case_id: 022-thermostat-sensor-decoupling
title: Thermostat Sensor Decoupling
primary_dimension: dependency_control
secondary_dimensions:
  - testability
language: C++
difficulty: easy-medium
loc: ~150
---

## Problem Context
A smart home controller decides whether to run heating, cooling, or stay idle based on a target temperature.
Right now, `ThermostatController` needs the current temperature passed in manually.
The product now needs thermostat decisions to read temperature from a provided hardware driver (`Tmp26Sensor`).

The design pressure is maintainability:
- connect hardware reading into the flow
- keep core decision logic decoupled from a hardware sensor type
- preserve easy testing of threshold behavior

## Given Code
Starter code provides:
- `src/thermostat_controller.h` / `.cc` with threshold policy logic
- `src/tmp26_sensor.h` / `.cc` with a hardware sensor simulation
- `app/main.cc` entrypoint
- evaluator tests and a structural dependency check

Initial state compiles and tests fail because the controller is not yet wired through a no-argument sensor based evaluate path.

## Agent-Facing Contract (This Text Must Match TASK.md)

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

## Expected Design Direction (Human-Facing)
A maintainable solution keeps `ThermostatController` independent from hardware sensor types.

Recommended shape:
- keep thermostat policy in `ThermostatController`
- inject temperature reading through an abstraction boundary (interface or callable)
- wire `Tmp26Sensor` in composition/runner code (for example in `main.cc`), not inside core policy files

Acceptable approaches include:
- an `ITemperatureSensor` interface passed into controller construction
- a `std::function<float()>` provider passed into the controller

This case does not require one exact class layout and allows for flexible implementations.

## Hidden Evaluator Intent
Primary maintainability probe:
- D6 Dependency Control

The evaluator rewards:
- correct heating/cooling/idle outcomes at threshold boundaries
- controller logic that does not include or reference `Tmp26Sensor` directly in business logic
- designs that keep policy testable through injected temperature sources

The evaluator penalizes:
- direct include of hardware sensor headers in thermostat core business logic files
- direct construction/reference of `Tmp26Sensor` in controller code
- removing `TMP26_SIMULATOR_TEMP` behavior from `tmp26_sensor.cc`

## Evaluation Criteria

### Functional
- no-argument evaluate path reads sensor temperature
- threshold rules are correct at and around `target +/- 2.0`
- behavior remains correct in app execution tests

### Structural
- enforced by `evaluator/022.thermostat-sensor-decoupling/checks/check_dependency.py`
- `thermostat_controller.h` / `.cc` must not include `tmp26_sensor.h`
- thermostat core files must not reference `Tmp26Sensor`
- `tmp26_sensor.cc` must preserve the `TMP26_SIMULATOR_TEMP` simulator behavior

### Maintainability
- dependency inversion between policy and hardware integration
- clear separation between core decision logic and hardware IO wiring
- testability remains deterministic and simple

## Oracle Signals
- Python functional tests verify thermostat command outputs via app-level execution
- structural dependency check catches hardware sensor coupling in core files
- thermostat core API/fields expose an abstraction seam (interface/callable/provider), not a hardware sensor type
- `Tmp26Sensor` wiring is allowed in composition code (for example `app/main.cc`) and rejected in thermostat core files
- `tmp26_sensor.cc` preserves `TMP26_SIMULATOR_TEMP` simulation behavior for deterministic evaluator execution
- `Evaluate()` with no arguments is present and called by the app harness

## Common Failure Modes (Non-Scoring)
- including `tmp26_sensor.h` in `thermostat_controller.cc` or `.h`
- instantiating `Tmp26Sensor` directly inside controller methods
- `Evaluate()` with arguments is not called by the app harness
- editing evaluator tests or checks instead of fixing architecture
- deleting the `TMP26_SIMULATOR_TEMP` sensor simulation behavior

## Distinctness and Mapping
Primary Dimension:
- D6 Dependency Control

Measured Capability:
- isolate policy logic from hardware-specific dependencies
- integrate hardware sensor behavior through an abstract way

Secondary Dimensions:
- D7 Testability and Determinism (non-scoring support)

Why this case is different from similar cases:
- compared with `008 map-dip` (D6 micro): both test dependency inversion, but `022` is specifically about keeping core business logic free of hardware sensor coupling.
- compared with `015 pipeline-provider-decoupling` (D6 multi-step): `015` covers a larger provider pipeline, while `022` is a small, focused controller-level dependency boundary check.

## Allowed & Disallowed Summary
| Action | Allowed |
|---|---|
| Add new files | Yes |
| Modify existing core logic | Yes |
| Modify existing tests | No (evaluator-owned) |
| Add new dependencies | No |
| Modify public headers | Yes |
| Use global mutable state | No |
| Introduce new external IO | No |
