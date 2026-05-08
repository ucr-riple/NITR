## Task

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
