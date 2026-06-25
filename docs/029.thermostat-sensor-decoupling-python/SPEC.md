---
case_id: 029-thermostat-sensor-decoupling-python
title: Thermostat Sensor Decoupling, Python
primary_dimension: dependency_control
secondary_dimensions:
  - testability
language: Python
granularity: micro
paired_with: 022.thermostat-sensor-decoupling
difficulty: easy-medium
loc: ~120-180
---

# Case 029: Thermostat Sensor Decoupling, Python

## Problem Context

A smart home controller decides whether to run heating, cooling, or stay idle based on a target temperature.
Right now, `ThermostatController` needs the current temperature passed in manually.
The product now needs thermostat decisions to read temperature from a provided hardware driver (`Tmp26Sensor`).

The design pressure is maintainability:

- connect hardware reading into the flow
- keep core decision logic decoupled from a hardware sensor type
- preserve easy testing of threshold behavior

## Case metadata and matrix rationale

- Case id / slug: `029-thermostat-sensor-decoupling-python`
- Title: `Thermostat Sensor Decoupling, Python`
- Primary dimension: `D6 Dependency Control`
- Secondary dimensions: `D7 Testability and Determinism`
- Granularity: `micro`
- Paired with: `022.thermostat-sensor-decoupling`
- Difficulty: `easy-medium`

Rationale for inclusion:

- This case is a Python paired port of case `022.thermostat-sensor-decoupling`.
- It preserves the same dependency-control probe while checking whether the benchmark can detect hardware coupling without relying on C++ include boundaries.
- The central question is unchanged: does core thermostat policy remain independent from the concrete sensor driver, or does hardware-specific reading leak into controller logic?

## Given code

The starter repository should run successfully and all provided tests should pass once the controller is wired through a sensor-backed no-argument evaluate path.

Expected starter shape:

```text
- cases/029.thermostat-sensor-decoupling-python/app/main.py
- cases/029.thermostat-sensor-decoupling-python/src/thermostat_controller.py
- cases/029.thermostat-sensor-decoupling-python/src/tmp26_sensor.py
- cases/029.thermostat-sensor-decoupling-python/TASK.md
- cases/029.thermostat-sensor-decoupling-python/CMakeLists.txt
- evaluator/029.thermostat-sensor-decoupling-python/pipeline.json
- evaluator/029.thermostat-sensor-decoupling-python/tests/test_thermostat.py
- evaluator/029.thermostat-sensor-decoupling-python/checks/run_evaluator.py
- docs/029.thermostat-sensor-decoupling-python/SPEC.md
```

Starter design assumptions:

- `ThermostatController` owns threshold policy logic
- `Tmp26Sensor` simulates a hardware temperature source and preserves the `TMP26_SIMULATOR_TEMP` environment hook
- the app currently reads the sensor manually and passes the temperature into the controller
- the starter leaves room for a poor solution that imports or instantiates the concrete sensor directly inside controller logic

The Python starter should make the wrong move attractive: reading environment state or using `Tmp26Sensor` directly inside thermostat core policy code.

## Agent-facing contract

The following section is the full text of `TASK.md`. The internal sections that follow are not exposed to the coding agent.

## Task

The `ThermostatController` currently requires the current room temperature to be passed into its evaluation function manually. We need to automate this by hooking it up to our new hardware sensor.

Update the code so that the thermostat controller can be connected to a temperature source, so callers no longer need to read the sensor and pass the value manually.

### Requirements

- Add a no-argument `evaluate()` method in `ThermostatController`.
- If the current temperature read from the sensor is 2.0 degrees (or more) below the target temperature, return `Command.HEATING`.
- If the current temperature read from the sensor is 2.0 degrees (or more) above the target temperature, return `Command.COOLING`.
- Otherwise, return `Command.IDLE`.

### Constraints

- Do not add external dependencies.
- Do not modify files under `evaluator`.
- You may modify or add new files under `src/` and `app/`.
- If you modify `src/tmp26_sensor.py`, preserve the `TMP26_SIMULATOR_TEMP` behavior.
- The project must run, and all existing tests must pass after the change.

## Expected design direction (human-facing)

A maintainable solution keeps `ThermostatController` independent from hardware sensor types.

Recommended shape:

- keep thermostat policy in `ThermostatController`
- inject temperature reading through an abstraction boundary such as a provider callable or minimal sensor protocol
- wire `Tmp26Sensor` in composition or runner code (for example `app/main.py`), not inside core policy files

Acceptable approaches include:

- a provider callable passed into controller construction
- a small abstract sensor interface or protocol

This case does not require one exact class layout and allows for flexible implementations.

## Hidden evaluator intent

Primary maintainability probe:

- D6 Dependency Control

The core question is whether thermostat policy stays testable and independent from concrete hardware reading logic, or whether environment-specific sensor behavior leaks into controller code.

The no-argument `evaluate()` path should read temperature through an injected or delegated boundary rather than by directly embedding hardware-specific knowledge in core policy logic.

## Functional expectations

The finished implementation should support:

- no-argument `evaluate()` reads sensor temperature
- threshold rules are correct at and around `target +/- 2.0`
- behavior remains correct in app execution tests

## Structural / oracle checks

Recommended checks:

- controller core logic should remain free of direct `Tmp26Sensor` coupling
- controller core logic should remain free of direct environment-variable reads
- simulator-specific environment behavior should remain localized to the sensor boundary
- application wiring should use the no-argument `evaluate()` path rather than manually reading temperature and forwarding it

These checks should remain secondary to functional correctness, but they are the core maintainability signal for the case.

## Common failure modes (non-scoring)

- embedding concrete sensor construction inside controller logic
- reading `TMP26_SIMULATOR_TEMP` directly inside policy code
- keeping the old manual read-and-forward path in the application
- solving the task by hard-coding app behavior instead of preserving the hardware seam

## Maintainability mapping

Primary Dimension:

- D6 Dependency Control

Measured Capability:

- isolate policy logic from hardware-specific dependencies
- integrate hardware sensor behavior through an abstract boundary

Secondary Dimensions:

- D7 Testability and Determinism

Why this case is different from similar cases:

- Compared with `008.map-dip`, both test dependency inversion, but `029` specifically focuses on preventing hardware sensor coupling inside a small controller.
- Compared with `015.pipeline-provider-decoupling`, `029` is a compact controller-level dependency boundary rather than a broader provider pipeline case.

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new files | Yes |
| Modify existing core logic | Yes |
| Modify existing tests | No (evaluator-owned) |
| Add new dependencies | No |
| Modify public APIs | Yes |
| Use global mutable state | No |
| Introduce new external IO | No |
