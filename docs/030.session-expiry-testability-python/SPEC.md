---
case_id: 030-session-expiry-testability-python
title: Session Expiry Testability, Python
primary_dimension: testability
secondary_dimensions:
  - dependency_control
  - change_locality
language: Python
granularity: micro
paired_with: 009.session-expiry-testability
difficulty: easy-medium
loc: ~100-160
---

# Case 030: Session Expiry Testability, Python

## Problem Context

We need a small `SessionManager` that creates sessions, checks expiry against a TTL,
refreshes valid sessions, and removes sessions.

The maintainability pressure is not the TTL rule itself. The real question is whether
time-driven behavior remains deterministic and cheap to test. Python implementations
often drift toward calling `time.time()` directly inside business logic, which makes
boundary-condition tests harder to write and encourages sleep-based validation.

## Case metadata and matrix rationale

- Case id / slug: `030-session-expiry-testability-python`
- Title: `Session Expiry Testability, Python`
- Primary dimension: `D7 Testability and Determinism`
- Secondary dimensions: `D6 Dependency Control`, `D1 Change Locality`
- Granularity: `micro`
- Paired with: `009.session-expiry-testability`
- Difficulty: `easy-medium`

Rationale for inclusion:

- This case is a Python paired port of case `009.session-expiry-testability`.
- It preserves the same maintainability probe while adapting the seam from a C++
  `TimeSource` interface to a Python time provider dependency.
- It checks whether evaluator infrastructure can recognize deterministic time control
  without relying on C++ type signatures.

## Given code

Expected starter shape:

```text
- cases/030.session-expiry-testability-python/app/main.py
- cases/030.session-expiry-testability-python/src/session_manager.py
- cases/030.session-expiry-testability-python/src/time_source.py
- cases/030.session-expiry-testability-python/TASK.md
- cases/030.session-expiry-testability-python/CMakeLists.txt
- evaluator/030.session-expiry-testability-python/pipeline.json
- evaluator/030.session-expiry-testability-python/tests/test_session_manager.py
- evaluator/030.session-expiry-testability-python/checks/run_evaluator.py
- docs/030.session-expiry-testability-python/SPEC.md
```

Starter design assumptions:

- `SessionManager` already accepts a `time_source` dependency, but the expiry logic is
  incomplete.
- `SystemTimeSource` remains the real-time adapter and should be the only place that
  touches wall-clock APIs.
- The starter should make the maintainable path obvious without revealing evaluator
  intent in `TASK.md`.

## Agent-facing contract

The following section is the full text of `TASK.md`. The internal sections that follow
are not exposed to the coding agent.

## Task

Implement a small `SessionManager`.

A session has an id and a TTL in seconds.
Support:
- creating a session
- checking whether a session is currently valid
- refreshing a valid session so its validity window restarts
- removing a session

Rules:
1. A session is valid immediately after creation.
2. A session becomes invalid once the elapsed time since creation or the most recent refresh reaches the TTL.
3. Refreshing a missing or expired session should fail.
4. Removing a session makes later validity checks fail.

Keep the implementation small and readable.

## Expected design direction (human-facing)

A maintainable solution keeps session-expiry rules independent from real wall-clock
reads.

Recommended shape:

- keep time access behind `TimeSource` or an equivalent injected provider
- keep TTL and refresh rules inside `SessionManager`
- make boundary-condition tests possible without sleeping

`SessionManager` should resolve the current time through its injected owner-side time
dependency when answering expiry and refresh questions, rather than reaching out to
`time.time()` or similar APIs from session-domain logic.

`time_source.py` should remain a thin real-time adapter. It may provide the concrete
wall-clock read and the minimal seam needed for injection, but it should not become a
second home for expiry policy, test-only freeze/setter APIs, or environment-driven
time overrides.

## Hidden evaluator intent

Primary maintainability probe:

- D7 Testability and Determinism

The core question is whether time-based behavior can be tested precisely and cheaply,
or whether business logic couples itself to real time and pushes tests toward waiting.

## Functional expectations

The finished implementation should support:

- newly created sessions are valid immediately
- expiry occurs exactly when elapsed time reaches TTL
- refreshing a valid session restarts the TTL window
- refreshing an expired or missing session fails
- removing a session invalidates it

## Structural / oracle checks

Recommended checks:

- non-adapter files under `src/` should not read wall-clock time directly
- real-time APIs should stay localized to `time_source.py`
- evaluator tests should advance a manual clock rather than sleep
- avoid evaluation-only backdoors such as `set_now_for_test`
- `SessionManager` should retain a constructor seam that accepts `time_source`
- `time_source.py` should retain a minimal `TimeSource` / `SystemTimeSource` adapter shape

These checks should remain secondary to functional correctness, but they are the core
maintainability signal for the case.

## Common failure modes (non-scoring)

- calling `time.time()` directly from `SessionManager`
- adding a test-only setter instead of using the existing time seam
- writing slow or flaky tests that wait for real time to pass
- scattering time reads across multiple methods instead of using one injected source

## Maintainability mapping

Primary Dimension:

- D7 Testability and Determinism

Measured Capability:

- make time-driven behavior deterministic without sleep
- preserve a clean seam between session rules and wall-clock access

Secondary Dimensions:

- D6 Dependency Control
- D1 Change Locality

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
