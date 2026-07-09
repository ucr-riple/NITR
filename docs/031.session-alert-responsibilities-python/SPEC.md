---
case_id: 031-session-alert-responsibilities-python
title: Session Alert Responsibilities, Python
primary_dimension: responsibility_decomposition
secondary_dimensions: []
language: Python
granularity: micro
paired_with: 025.session-alert-responsibilities
difficulty: easy-medium
loc: ~120-200
---

# Case 031: Session Alert Responsibilities, Python

## Problem Context

A telemetry session monitor scans a sequence of events and reports anomalies.
The monitor already reports out-of-range samples. It now needs to add two more
independent anomaly families:

- drift alerts, which compare later samples against a per-channel baseline
- leak alerts, which summarize unmatched acquire/release pairs at end of session

The design pressure is maintainability, not just feature completion. These
three families share the same event stream, but they do not share the same
state model or output shape. Range is stateless per event, drift owns a
baseline map, and leak owns open/close balance plus end-of-stream
finalization. The maintainability risk is that all three get piled into one
thick `analyze()` function or one combined helper simply because they happen to
look at the same input.

## Case metadata and matrix rationale

- Case id / slug: `031-session-alert-responsibilities-python`
- Title: `Session Alert Responsibilities, Python`
- Primary dimension: `D3 Responsibility Decomposition`
- Secondary dimensions: none
- Granularity: `micro`
- Paired with: `025.session-alert-responsibilities`
- Difficulty: `easy-medium`

Rationale for inclusion:

- This case is a Python paired port of case `025.session-alert-responsibilities`.
- It preserves the same D3 probe while adapting the structural oracle from
  brace-matched C++ functions to Python functions and methods.
- The central question is unchanged: does the agent give each alert family its
  own unit, or does it turn one existing analysis entrypoint into a
  responsibility tangle?

## Given code

Expected starter shape:

```text
- cases/031.session-alert-responsibilities-python/app/main.py
- cases/031.session-alert-responsibilities-python/src/monitor.py
- cases/031.session-alert-responsibilities-python/TASK.md
- cases/031.session-alert-responsibilities-python/CMakeLists.txt
- evaluator/031.session-alert-responsibilities-python/pipeline.json
- evaluator/031.session-alert-responsibilities-python/tests/test_monitor.py
- evaluator/031.session-alert-responsibilities-python/checks/run_evaluator.py
- docs/031.session-alert-responsibilities-python/SPEC.md
```

Starter design assumptions:

- `analyze()` currently implements only range alerts
- the starter is intentionally clean and short rather than already tangled
- the wrong move should be attractive: adding drift and leak directly into
  `analyze()` or a single `detect_all_alerts()` helper

## Agent-facing contract

The following section is the full text of `TASK.md`. The internal sections that
follow are not exposed to the coding agent.

## Task

### Context

`analyze()` (implemented in `src/monitor.py`) scans a sequence of telemetry
events from a single monitoring session and returns a `Report` describing the
anomalies it found. Each `Event` carries a `channel` name, a `kind`
(`EventKind.SAMPLE`, `EventKind.ACQUIRE`, or `EventKind.RELEASE`), and a
`value` (meaningful only for sample events). The `Config` carries `low_bound`,
`high_bound`, and `drift_tolerance`.

Today `analyze()` reports only out-of-range readings: every sample whose value
falls strictly outside `[low_bound, high_bound]` produces a `RangeAlert`.

### Requirements

Extend `analyze()` so the returned `Report` is also populated with two further
kinds of anomalies, alongside the existing range alerts:

1. **Drift alerts.** The first sample observed on a channel establishes that
   channel's baseline value. For every later sample on the same channel whose
   value differs from that channel's baseline by strictly more than
   `drift_tolerance`, add a `DriftAlert(channel, value, baseline)`. The
   baseline reading itself never produces a drift alert. Events that are not
   sample events do not affect drift.

2. **Leak alerts.** An acquire event opens a channel and a release event closes
   it. A channel that has been opened more times than it has been closed by the
   end of the session is still open; add exactly one `LeakAlert(channel)` for
   each such channel.

### Output ordering

- `range_alerts` and `drift_alerts` must appear in the order in which their
  triggering sample events occur in the input.
- `leak_alerts` must be ordered by channel name, ascending.
- Calling `analyze()` again with the same input must produce an identical
  `Report`.

### Constraints

- Do not change the existing range-alert behavior, and do not change the public
  types in `src/monitor.py` (`Event`, `Config`, `RangeAlert`, `DriftAlert`,
  `LeakAlert`, `Report`, `EventKind`) — the tests depend on them.
- Implement the change in the files under `src/`. You may add new files,
  functions, or types, but do not modify files outside this directory.
- Do not add external dependencies.

## Expected design direction (human-facing)

This is a responsibility decomposition probe. Each anomaly family should be
owned by its own focused unit, with `analyze()` acting as a thin orchestrator.

Recommended shape:

- give drift production its own helper/function/class
- give leak production its own helper/function/class
- keep range production separate rather than fusing all three families

The important constraint is not one exact Python layout. The important
constraint is that no single function should own multiple alert families.

## Hidden evaluator intent

Primary maintainability probe:

- D3 Responsibility Decomposition

The core question is whether three distinct responsibilities remain separated
even though they scan the same input stream, or whether feature pressure turns
the analysis into one combined function.

## Functional expectations

The finished implementation should support:

- range alerts for out-of-range samples
- drift alerts using the first per-channel sample as baseline
- leak alerts for channels still open at end of session
- stable ordering and deterministic repeated results

## Structural / oracle checks

Recommended checks:

- no single function should produce more than one alert family
- each family must be produced by code reachable from `analyze()`
- direct report-vector appends and alert-type construction should both count as
  family production signals
- whole-vector routing/assignment in a thin orchestrator should not be treated
  as a family-production signal

These checks should remain secondary to functional correctness, but they are
the core maintainability signal for the case.

## Common failure modes (non-scoring)

- putting range, drift, and leak logic into `analyze()`
- moving the same tangle into one `detect_all_alerts()` helper
- fusing two families into one helper and only separating the third
- adding dead helpers for one family without wiring them into `analyze()`

## Maintainability mapping

Primary Dimension:

- D3 Responsibility Decomposition

Measured Capability:

- keep independent responsibilities in separate units
- resist turning one existing entrypoint into a multi-concern monolith

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new files | Yes |
| Modify existing core logic | Yes |
| Modify existing tests | No (evaluator-owned) |
| Add new dependencies | No |
| Modify public APIs | No for existing public types |
| Use global mutable state | No |
