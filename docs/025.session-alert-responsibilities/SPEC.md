---
case_id: 025
title: Session Alert Responsibilities
primary_dimension: D3
secondary_dimensions: []
language: C++
difficulty: 3
loc: 120
---

## Problem context

This case is derived from a real maintainability smell in the [SemLoc](https://github.com/jerry729/SemLoc) research code . In
`instrumentation.py`, the class `ReturnSiteHandler.plan` is a single ~100-line
method that interleaves **three unrelated emission responsibilities** at each
return site: expression checks (`EXPR` categories), temporal call-snapshot
checks (`TEMPORAL_CALL_SNAPSHOT`), and temporal until-overwritten tracking
(`TEMPORAL_UNTIL_OVERWRITTEN` write/read/kill). The three concerns have
different state and different output shapes; they were fused into one method
only because they happen to share a location (the return site). The same
codebase elsewhere keeps per-concern logic in focused `Handler` units
(`EntryExprHandler`, `LoopTailExprHandler`, …) registered in `Instrumenter`, so
the monolithic return-site method is a genuine responsibility-decomposition
drift, not a deliberate design.

The C++ reproduction keeps the language-agnostic essence: a single function
that scans a stream of records and is under pressure to compute several
independent result families in one place. Here the domain is a telemetry
**session monitor**. `analyze()` scans a sequence of `Event`s and produces a
`Report` with three independent anomaly families:

- **range** — a `Sample` whose value is strictly outside `[low_bound, high_bound]`;
- **drift** — a `Sample` that deviates from its channel's first-seen baseline by
  more than `drift_tolerance`;
- **leak** — a channel acquired more often than released by end of session.

The three families have genuinely different shapes: range is stateless per
event, drift needs a per-channel baseline, and leak needs balance tracking plus
an end-of-stream finalization. They are not interchangeable variants of one
operation (which would be a D4 extension-structure problem); they are distinct
responsibilities (D3).

## Starter state

The starter is intentionally clean and minimal: `analyze()` implements only the
range family, in a single short loop. It compiles and the range portion behaves
correctly. The starter does **not** pre-contain the smell — there is no giant
function, no tangle, and no pre-built decomposition seam that would hint at the
intended design. The smell only appears if the agent, when adding the two new
families, piles them into `analyze()` (or into one combined helper) instead of
giving each family its own unit.

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

## Expected design direction

The exercise tests responsibility decomposition (D3): each anomaly family should
be owned by its own focused unit (free function, helper, or class), with
`analyze()` acting as a thin orchestrator that composes their results. A typical
correct solution will:

1. Add a drift producer and a leak producer as separate units, each owning only
   its family's state and output.
2. Leave the existing range logic intact, either as its own unit or inline in a
   `analyze()` that owns no other family.
3. Keep `analyze()` from becoming a single function that assembles all three
   families.

Both a cleanly decomposed solution and a tangled one (all three families inside
`analyze()` or one `detect_all` helper) are functionally identical, so the
structural check is the oracle for the dimension.

## Evaluation criteria

* **Functional correctness** (`tests/test_monitor.cpp`). Range, drift, and leak
  detection are checked for correctness, required ordering (range/drift in event
  order, leaks sorted by channel), and determinism (a repeated call yields an
  identical `Report`). The starter passes the range assertions but fails the
  drift/leak assertions until the feature is implemented.
* **Structural decomposition** (via `evaluator/025.session-alert-responsibilities/pipeline.json`
  and its remaining `customized_check`). No single
  function may produce more than one alert family.

## Oracle signals and failure modes

### Functional tests (`test_monitor.cpp`)

1. Range-only scenario (drift tolerance large, no acquire/release).
2. Drift scenario across two channels, asserting per-channel baseline and event
   ordering.
3. Leak scenario with balanced and unbalanced channels, asserting leaks are
   sorted by channel and that samples do not affect leak accounting.
4. Mixed scenario plus a determinism check (two calls compared).

### Structural decomposition check

The remaining custom structural check parses each function/method body
(brace-matched; control blocks are skipped by keyword) and computes which alert
families it *produces*. A family is produced if the body:

1. Names that family's alert type (e.g. `RangeAlert`), or
2. Appends to its report vector directly (`range_alerts.push_back(...)` /
   `.emplace_back(...)`), or
3. Appends through a **reference alias** bound to that vector:
   - Member-binding aliases: `auto& r = report.range_alerts; r.push_back(...)`
   - Typed vector aliases: `std::vector<RangeAlert>& r = ...; r.push_back(...)`

Reads/assignments of a whole vector (`report.range_alerts = ...`) are
deliberately **not** signals, so a thin orchestrator that only routes results is
never flagged.

The checker also builds a **call graph** from `analyze()` and only counts
families produced by functions **reachable** from the entry point. Dead helper
functions that are never called do not satisfy the positive requirement.

* **Negative — one function, multiple families forbidden**: any function whose
  body produces ≥2 of {range, drift, leak} is a responsibility tangle. This
  catches the full monolith (everything in `analyze`), the moved monolith
  (a single `detect_all` helper), and partial tangles (e.g. range+drift fused).
* **Positive — every family must be produced by reachable code**: each family
  must be produced by at least one function reachable from `analyze()` (directly
  or transitively). Guards against unfinished solutions and dead-code padding.

### Why the tangle passes all functional tests

Computing range, drift, and leak inside one loop produces exactly the same
`Report` as three separate passes. Ordering and determinism hold either way. The
D3 violation is invisible to behavior; only the structural check exposes it.

### Common solution shapes and outcomes

| Shape | Structural result |
|---|---|
| Three separate producer functions, thin `analyze` | pass |
| Fill-by-reference producers (`emplace_back` without naming the type) | pass |
| Per-family classes with one `feed`/`finish` method each | pass |
| `analyze` keeps range inline, delegates drift + leak | pass |
| All three families inside `analyze` (the primary tangle) | fail |
| One `detect_all` helper doing all three | fail |
| Two families fused in one helper (e.g. range + drift) | fail |

### Known false positive

If a solution makes `analyze()` itself loop and `push_back`/`emplace_back`
results for **all three** families (rather than assigning whole vectors returned
by producers), the orchestrator would be flagged even though the per-family
computation lives in helpers. This loop-and-copy orchestration style is uncommon
and should be treated by human reviewers as an acceptable near-miss when the
real per-family logic is in separate units.

### Oracle limitations

The structural checker uses regex-based pattern matching with alias tracking and
reachability analysis. While it catches common responsibility tangles and
prevents straightforward bypass attempts (direct aliasing, dead-code padding),
some edge cases may still evade detection:

1. **Other container mutation APIs**: using `insert()`, `assign()`, `resize()`,
   or other non-`push_back` / non-`emplace_back` append paths.
2. **Helper-return aliasing**: a monolithic function can obtain a family's alert
   vector through a helper return value, for example `auto& r = get_ranges(report);
   r.emplace_back(...)`. The checker tracks aliases bound directly from
   `report.range_alerts` / `drift_alerts` / `leak_alerts` and explicit typed
   vector aliases, but does not prove that an arbitrary helper return value is
   one of those vectors.
3. **Multi-level aliasing**: `auto& r1 = report.range_alerts; auto& r2 = r1;
   r2.push_back(...)` (only one level of aliasing is tracked).
4. **Lambda or function-pointer indirection**: capturing alert vectors in
   lambdas and invoking them within a monolithic function.

These patterns are outside the checker’s intended coverage. The oracle is meant
to distinguish typical well-decomposed solutions from typical responsibility
tangles, not to provide perfect adversarial robustness against every possible
C++ indirection style.

---

This case specifically exercises **D3 (responsibility decomposition)** by
hiding the pressure inside a plain "add two more outputs" request, where the
path of least resistance is to thicken the one function that already exists.
Other dimensions are out of scope unless they naturally arise.
