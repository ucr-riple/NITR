---
case_id: 032-metric-recorder-buffered-flush-python
title: Metric Recorder Buffered Flush, Python
primary_dimension: interface_substitutability
secondary_dimensions:
  - extensibility
  - state_lifecycle
language: Python
granularity: micro
paired_with: 024.metric-recorder-buffered-flush
difficulty: medium
loc: ~120-200
---

# Case 032: Metric Recorder Buffered Flush, Python

## Problem Context

A backend service emits metrics from many call sites via a `MetricRecorder`
reference. The only deployed implementation, `ConsoleMetricRecorder`, writes
each metric immediately. The product now needs a buffered recorder for
high-throughput services plus a checkpoint-visibility trigger that works
regardless of which recorder implementation is wired in.

## Case metadata and matrix rationale

- Case id / slug: `032-metric-recorder-buffered-flush-python`
- Title: `Metric Recorder Buffered Flush, Python`
- Primary dimension: `D5 Interface and Substitutability Discipline`
- Secondary dimensions: `D4 Extension Structure`, `D8 State Ownership and Lifecycle`
- Granularity: `micro`
- Paired with: `024.metric-recorder-buffered-flush`
- Difficulty: `medium`

Rationale for inclusion:

- This case is a Python paired port of case `024.metric-recorder-buffered-flush`.
- It preserves the same substitutability probe while adapting the class-shape
  oracle from C++ inheritance checks to Python classes and abstract methods.
- The central question is unchanged: can the consumer invoke the new
  visibility trigger through the existing abstraction, or does it need to
  discover the concrete recorder type?

## Given code

Expected starter shape:

```text
- cases/032.metric-recorder-buffered-flush-python/app/main.py
- cases/032.metric-recorder-buffered-flush-python/src/metric_recorder.py
- cases/032.metric-recorder-buffered-flush-python/src/console_metric_recorder.py
- cases/032.metric-recorder-buffered-flush-python/src/metric_collector.py
- cases/032.metric-recorder-buffered-flush-python/TASK.md
- cases/032.metric-recorder-buffered-flush-python/CMakeLists.txt
- evaluator/032.metric-recorder-buffered-flush-python/pipeline.json
- evaluator/032.metric-recorder-buffered-flush-python/tests/test_recorder_lifecycle.py
- evaluator/032.metric-recorder-buffered-flush-python/checks/run_evaluator.py
- docs/032.metric-recorder-buffered-flush-python/SPEC.md
```

Starter design assumptions:

- `MetricRecorder` currently exposes only `record()`
- `ConsoleMetricRecorder` preserves immediate-write behavior
- `MetricCollector` works through a recorder reference and currently has no
  checkpoint method
- the starter leaves room for the wrong move: adding flush/visibility only to
  `BufferedMetricRecorder` and then branching in the consumer

## Agent-facing contract

The following section is the full text of `TASK.md`. The internal sections that
follow are not exposed to the coding agent.

## Task

A new operational requirement: high-throughput services need to record many
metrics per second, and writing each metric immediately is too slow. Add a
`BufferedMetricRecorder` that accumulates metrics and writes them in a single
batch when its capacity is reached or when the consumer explicitly requests
visibility.

A second new requirement: between request batches, the system runs a
checkpoint. Downstream tooling reads metric output to verify that all metrics
from the just-finished batch are visible *before* the checkpoint releases.
With buffering, the consumer needs an explicit visibility trigger at the
checkpoint boundary that works regardless of which recorder implementation is
wired in.

### Requirements

- Add a `BufferedMetricRecorder` that buffers up to a configurable capacity of
  metrics and writes them in one batch to the underlying stream when capacity
  is reached or when visibility is explicitly requested.
- The new `BufferedMetricRecorder` should be constructible from the target
  output stream plus a buffer capacity.
- Add an explicit visibility trigger that can be invoked to make any queued
  metrics visible immediately, supporting the checkpoint scenario below.
- Add a `checkpoint()` method to `MetricCollector` that the consumer can call
  at the checkpoint boundary to guarantee visibility of all queued metrics,
  regardless of which recorder implementation is wired in.
- Existing deployments that use `ConsoleMetricRecorder` must continue to work
  without changes to their consumer code.
- We expect to add network-backed and disk-backed metric recorders in upcoming
  sprints. The `MetricCollector` should not need code changes for each new
  recorder type.

### Constraints

- Do not modify files under `evaluator`.
- You may add new files under `src`.
- Keep existing `ConsoleMetricRecorder` immediate-write behavior unchanged.
- Do not add external dependencies.

## Expected design direction (human-facing)

A maintainable solution preserves substitutability between the existing
recorder and any new buffered recorder.

Recommended shape:

- extend the abstract base with a polymorphic visibility-trigger such as
  `flush()`
- allow the consumer to invoke that trigger through the abstract base
- keep buffer-management state inside the buffered implementation

Undesirable directions:

- adding the visibility-trigger only to the buffered subclass
- introducing capability predicates such as `is_buffered()`
- making `MetricCollector` branch on concrete recorder types
- hiding visibility only in destructor-time flushing

## Hidden evaluator intent

Primary maintainability probe:

- D5 Interface and Substitutability Discipline

The core question is whether the abstraction evolves to admit a new use case
while preserving consumer-side substitutability, or whether the new recorder
forces concrete-type knowledge upward.

## Functional expectations

The finished implementation should support:

- immediate-write recorder still surfaces metrics as they are recorded
- buffered recorder defers visibility until capacity or explicit flush
- buffered recorder flushes when capacity is reached
- `checkpoint()` works through the abstract recorder reference
- `checkpoint()` is harmless for the immediate-write recorder

## Structural / oracle checks

Recommended checks:

- `MetricRecorder` should declare a polymorphic visibility-trigger in addition
  to `record()`
- `BufferedMetricRecorder` should derive from the same abstract base
- `MetricCollector` must not reference concrete recorder types
- `MetricCollector` must not use `isinstance()` or capability branching to
  decide whether visibility can be triggered
- the buffered implementation should own its own buffer and capacity state

These checks should remain secondary to functional correctness, but they are
the core maintainability signal for the case.

## Common failure modes (non-scoring)

- adding `flush()` only on `BufferedMetricRecorder`
- branching in `MetricCollector` on `isinstance(recorder, BufferedMetricRecorder)`
- capability probing such as `hasattr(recorder, "flush")` followed by
  conditional behavior
- merging buffering into `ConsoleMetricRecorder` behind a flag

## Maintainability mapping

Primary Dimension:

- D5 Interface and Substitutability Discipline

Measured Capability:

- evolve an existing abstraction to admit a new implementation
- preserve abstraction-only consumer behavior at the new call site
- keep new state on the implementation that needs it

Secondary Dimensions:

- D4 Extension Structure
- D8 State Ownership and Lifecycle

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new files under `src/` | Yes |
| Modify existing core logic | Yes |
| Modify existing tests | No (evaluator-owned) |
| Add new dependencies | No |
| Modify public interfaces | Yes, where required by the abstraction |
| Use global mutable state | No |
