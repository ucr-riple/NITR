## Task

### Context

`analyze()` (declared in `src/monitor.h`, implemented in `src/monitor.cc`) scans a
sequence of telemetry events from a single monitoring session and returns a
`Report` describing the anomalies it found. Each `Event` carries a `channel`
name, a `kind` (`Sample`, `Acquire`, or `Release`), and a `value` (meaningful
only for `Sample` events). The `Config` carries `low_bound`, `high_bound`, and
`drift_tolerance`.

Today `analyze()` reports only out-of-range readings: every `Sample` whose value
falls strictly outside `[low_bound, high_bound]` produces a `RangeAlert`.

### Requirements

Extend `analyze()` so the returned `Report` is also populated with two further
kinds of anomalies, alongside the existing range alerts:

1. **Drift alerts.** The first `Sample` observed on a channel establishes that
   channel's baseline value. For every later `Sample` on the same channel whose
   value differs from that channel's baseline by strictly more than
   `drift_tolerance`, add a `DriftAlert{channel, value, baseline}`. The baseline
   reading itself never produces a drift alert. Events that are not `Sample`
   events do not affect drift.

2. **Leak alerts.** An `Acquire` event opens a channel and a `Release` event
   closes it. A channel that has been opened more times than it has been closed
   by the end of the session is still open; add exactly one `LeakAlert{channel}`
   for each such channel.

### Output ordering

- `range_alerts` and `drift_alerts` must appear in the order in which their
  triggering `Sample` events occur in the input.
- `leak_alerts` must be ordered by `channel` name, ascending.
- Calling `analyze()` again with the same input must produce an identical
  `Report`.

### Constraints

- Do not change the existing range-alert behaviour, and do not change the public
  types in `src/monitor.h` (`Event`, `Config`, `RangeAlert`, `DriftAlert`,
  `LeakAlert`, `Report`) — the tests depend on them.
- Implement the change in the files under `src/`. You may add new files,
  functions, or types, but do not modify files outside this directory.
- The solution must compile with standard C++17.
