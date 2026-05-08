# 024. metric-recorder-buffered-flush

## 1. Case Metadata

```yaml
case_id: 024-metric-recorder-buffered-flush
title: Metric Recorder Buffered Flush
primary_dimension: interface_substitutability
secondary_dimensions:
  - extensibility
  - state_lifecycle
language: C++
difficulty: medium
loc: ~150
```

## 2. Problem Context

A backend service emits metrics from many call sites. Components throughout
the codebase obtain a `MetricRecorder` reference and call `Record(metric)` to
publish counters and latency samples. Today the only deployed implementation
is `ConsoleMetricRecorder`, which writes each metric to a stream as it
arrives. The product is moving toward higher request throughput, where
per-metric writes are wasteful, and toward a periodic checkpoint discipline
where downstream tooling reads metric output between batches.

## 3. Given Code

The starter compiles and links into a small library plus a demo executable.
It contains:

- `src/metric_recorder.h` — abstract base class `MetricRecorder` with a single
  pure-virtual `Record(const Metric&)` method, plus the `Metric` value type.
- `src/console_metric_recorder.h` / `.cc` — concrete implementation that
  writes each metric immediately to a provided `std::ostream`.
- `src/metric_collector.h` / `.cc` — a small consumer that holds a
  `MetricRecorder&` reference, computes derived metrics from raw samples,
  and publishes them through the recorder.
- `app/main.cc` — wires a `ConsoleMetricRecorder` writing to `std::cout`,
  constructs a `MetricCollector`, and drives a single small batch.

The starter is the typical shape one would arrive at when only one delivery
path is needed. The new requirements below introduce a second delivery
shape and a checkpoint-visibility constraint that today's design does not
yet support.

## 4. Task (Agent-Facing)

The exact text below appears in both `SPEC.md` and `TASK.md`.

---

### Task

A new operational requirement: high-throughput services need to record many
metrics per second, and writing each metric immediately is too slow. Add a
`BufferedMetricRecorder` that accumulates metrics and writes them in a single
batch when its capacity is reached or when the consumer explicitly requests
visibility.

A second new requirement: between request batches, the system runs a
checkpoint. Downstream tooling reads metric output to verify that all
metrics from the just-finished batch are visible *before* the checkpoint
releases. With buffering, the consumer needs an explicit visibility trigger
at the checkpoint boundary that works regardless of which recorder
implementation is wired in.

### Requirements

- Add a `BufferedMetricRecorder` that buffers up to a configurable capacity
  of metrics and writes them in one batch to the underlying stream when
  capacity is reached or when visibility is explicitly requested.
- Add an explicit visibility trigger that can be invoked to make any queued
  metrics visible immediately, supporting the checkpoint scenario below.
- Add a `Checkpoint()` method to `MetricCollector` that the consumer can
  call at the checkpoint boundary to guarantee visibility of all queued
  metrics, regardless of which recorder implementation is wired in.
- Existing deployments that use `ConsoleMetricRecorder` must continue to
  work without changes to their consumer code.
- We expect to add network-backed and disk-backed metric recorders in
  upcoming sprints. The `MetricCollector` should not need code changes for
  each new recorder type.

### Constraints

- Do not modify files under `evaluator/024.metric-recorder-buffered-flush/`.
- You may add new files under `cases/024.metric-recorder-buffered-flush/src/`.
- Keep existing `ConsoleMetricRecorder` immediate-write behavior unchanged.
- The project must compile, and all evaluator tests must pass after the
  change.

---

## 5. Expected Design Direction (Human-Facing, Non-prescriptive)

A maintainable solution preserves substitutability between the existing
recorder and any new one. The visibility-trigger that the consumer needs
must work uniformly across all current and future recorder implementations,
which means the consumer should not have to discover or branch on the
concrete recorder type.

Acceptable design directions:

- Extend the abstract base with a polymorphic operation that any
  implementation can implement meaningfully (a no-op for immediate-write
  impls, a real flush for buffered impls).
- Allow the consumer to invoke that operation through the abstract base
  reference without knowing the concrete type.

Undesirable directions:

- Adding the visibility-trigger to a single concrete subclass and forcing
  the consumer to discover the concrete type.
- Introducing a predicate (such as `IsBuffered()`) on the base that
  callers branch on.
- Implementing buffering inside the existing immediate-write recorder
  controlled by a flag, mixing two responsibilities in one class.
- Relying solely on destructor-time flushing — the checkpoint scenario
  requires visibility while the recorder is still alive.

## 6. Evaluation Criteria

### 6.1 Functional

- The `MetricCollector` continues to publish derived metrics through its
  recorder reference.
- An immediate-write recorder still surfaces metrics as they are recorded.
- A buffered recorder defers visibility until either capacity is reached
  or an explicit visibility-trigger fires.
- The checkpoint-style visibility-trigger on `MetricCollector` works when
  the wired recorder is buffered, and is harmless when the wired recorder
  is immediate.

### 6.2 Structural

- The abstract base must admit the visibility-trigger as a polymorphic
  member, not a subclass-only method.
- All existing concrete recorders must implement the polymorphic
  visibility-trigger (an empty body is acceptable for immediate-write
  impls).
- The new buffered recorder must derive from the same abstract base as the
  existing recorder.
- `MetricCollector` must operate through the abstract recorder reference
  and must not reference any concrete recorder type by name.
- `MetricCollector` must not use `dynamic_cast` to reach the
  visibility-trigger.

### 6.3 Maintainability

- The decision to evolve the abstract base versus narrow the change to a
  subclass should be motivated by the substitutability constraint, not by
  any particular naming.
- Buffer-management state should live with the buffered recorder, not in
  unrelated classes.
- The consumer's checkpoint behavior should not require code changes when
  a third or fourth recorder implementation is added later.

## 7. Oracle Signals

The evaluator uses the following concrete signals:

1. Functional gtest cases:
   - immediate-write recorder still surfaces metrics
   - buffered recorder defers visibility before capacity / explicit trigger
   - buffered recorder flushes when capacity is reached
   - explicit visibility-trigger on a buffered recorder makes metrics visible
   - the consumer's checkpoint operation works through the abstract base
     reference when wired with a buffered recorder
2. Structural Python check (`check_substitutability.py`):
   - the abstract base declares at least one polymorphic visibility-trigger
     in addition to `Record`
   - a new buffered recorder header exists and derives from the abstract base
   - the buffered recorder overrides both `Record` and the
     visibility-trigger
   - the existing immediate-write recorder also overrides the
     visibility-trigger
   - `MetricCollector` does not reference any concrete recorder type
   - `MetricCollector` does not use `dynamic_cast`

## 8. Failure Modes (Non-scoring)

- declares the visibility-trigger only on the buffered subclass and uses
  `dynamic_cast` in the consumer
- introduces an `IsBuffered()` predicate on the base and branches on it
- implements buffering inside the immediate-write recorder behind a flag
- implements buffering only at destructor time, blocking the checkpoint
  scenario
- forwards visibility through a separate side channel (a global, an
  observer registry) instead of through the recorder abstraction
- accepts the buffered recorder as a concrete type in `MetricCollector`,
  preserving immediate-only support only by an overload

## 9. Maintainability Mapping

```text
Primary Dimension:
  - D5 Interface and Substitutability Discipline
Measured Capability:
  - evolve an existing abstraction to admit a new use case while
    preserving substitutability for prior implementations
  - keep consumer code abstraction-only at the new call site
  - place new state on the implementation that needs it, not on the base
Secondary Dimensions:
  - D4 Extension Structure (supporting)
  - D8 State Ownership and Lifecycle (supporting)
```

## 10. Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new files under `cases/024.metric-recorder-buffered-flush/src/` | Yes |
| Modify existing core logic | Yes, where required by the new behavior |
| Modify existing tests | No (evaluator-owned) |
| Add new dependencies | No |
| Modify public headers | Yes, where required by the abstraction |
| Use global mutable state | No |
| Introduce new external IO | No (the existing stream parameter is enough) |

## 11. Distinctness From Existing Cases

This case occupies a structural cell distinct from existing D5 cases and
from the case 022 sensor-decoupling shape:

- `006 gs-isp` narrows a wide shared type into per-consumer slices
  (interface segregation). This case enriches a thin abstract base.
- `007 ml-lsp` is multi-step substitution across an ML pipeline. This is
  single-step interface evolution.
- `022 thermostat-sensor-decoupling` introduces a new abstraction over a
  concrete dependency. This case evolves an abstraction that already
  exists, in order to admit a new implementation without breaking
  substitutability for the existing one.

The pressure point unique to this case is **adding a method to an abstract
base such that a no-op override on the existing implementation is the
right answer**. Many agents will instead add the method only to the new
subclass and reach for `dynamic_cast` in the consumer.
