# Case Specification

## 1. Case Metadata

```yaml
case_id:        ml-parameter-sweep-reuse
domain:         machine_learning_tooling
principle:      N/A  # MaintainBench: repo-awareness / pattern conformance
difficulty:     easy
language:       C++17
loc:            ~150-200
```

---

## 2. Problem Context

Experiment tracking tools often accumulate sweep functions on top of a shared trial runner.
A common failure mode is that engineers adding a new sweep reimplement trial execution or
aggregation logic inline rather than routing through the primitives that already exist in
the repository. A subtler failure is implementing the sweep's iteration and result structure
from scratch rather than recognising and mirroring the pattern already established by
existing sweeps.

This case uses a small benchmarking harness with one trial primitive, shared aggregation
helpers, and two fully-implemented sweeps to expose both failure modes in a single task.

---

## 3. Given Code

The repository provides:

- `src/runner.{h,cc}`: `run_trial(const TrialParams&) -> TrialResult` — the one shared
  trial execution primitive. Performs input validation, seeded deterministic noise
  generation, and a synthetic loss formula. This is the function all sweeps must route
  through.
- `src/aggregate.{h,cc}`: `compute_summary(...)` and `pick_best(...)` — shared aggregation
  helpers used by both existing sweeps.
- `src/sweeps.{h,cc}`: two fully-implemented sweeps (`sweep_learning_rate` and
  `sweep_batch_size_x_lr`) that establish the structural pattern the new sweep must follow.
- `app/main.cc`: frozen CLI dispatcher — do not modify.

---

## 4. Task Description

### Public API (Do Not Change)

Declared in `src/sweeps.h`:

```cpp
// Implement this.
SweepResult sweep_warmup_x_lr(const TrialParams& base,
                               const std::vector<int>& warmup_steps_grid,
                               const std::vector<double>& lr_grid);
```

### Task (TASK.md)

Add `sweep_warmup_x_lr` to `src/sweeps.cc`.

The sweep searches over a Cartesian product of warmup step counts and learning rates,
returning a `SweepResult` with one entry per `(warmup_steps, lr)` combination.

Requirements:
- One `SweepResult` entry per `(warmup_steps, lr)` combination.
- `configs`, `results`, `best_idx`, and `summary` populated in the same pattern as the
  existing sweeps (`sweep_learning_rate`, `sweep_batch_size_x_lr`).

**Expected design direction:** Mirror `sweep_batch_size_x_lr` structurally — outer loop
over the first axis, inner loop over the second, call `run_trial` per point, then call
`pick_best` and `compute_summary` on the accumulated results. The reuse pressure is
recognising and conforming to both the existing call pattern and the existing result
structure, not just calling the primitive.

### File restrictions

- You may modify: `src/sweeps.cc`
- You must not modify: `src/sweeps.h`, `src/runner.{h,cc}`, `src/aggregate.{h,cc}`,
  `app/main.cc`, or anything under `evaluator/024.reuse-parameter-sweep/`
- Do not add new source files for this case.

---

## 5. Evaluation Criteria

### 5.1 Functional

- Existing sweep tests must continue to pass.
- `sweep_warmup_x_lr` produces `warmup_steps_grid.size() * lr_grid.size()` results.
- Results are deterministic (same params → same output).
- `best_idx` is the index of the minimum-loss result.
- `summary` fields (`mean`, `min_loss`, `max_loss`) are correct.

### 5.2 Structural (Maintainability)

**Rule 1 — sweep_warmup_x_lr must delegate:**
- Body must contain a call to `run_trial(`.
- Body must contain a call to `pick_best(`.
- Body must contain a call to `compute_summary(`.
- Body must not contain runner-internal fingerprints (`0xDEADBEEF`, `log1p`,
  xorshift shift constants) — signals that trial execution was reimplemented inline.

**Rule 2 — frozen file:**
- `app/main.cc` must match the golden baseline exactly.

---

## 6. Failure Modes (Non-scoring)

Common incorrect solutions:
- Copying the trial logic from `runner.cc` directly into the new sweep instead of calling `run_trial()`.
- Writing a manual loop to find the best result instead of calling `pick_best()`.
- Forgetting to call `compute_summary()` at all.
- Filling `results` for each grid point but not filling `configs` in the same order.

---

## 7. Principle Mapping

```text
Mapping: MaintainBench D2 — Reuse and Repo Awareness
Measured Capability:
  - Recognise and mirror the established sweep pattern rather than reimplementing it
  - Delegate to existing primitives (run_trial, pick_best, compute_summary) rather than
    inlining equivalent logic
```

---

## 8. Allowed & Disallowed Summary

| Action                             | Allowed |
|------------------------------------|---------|
| Modify `src/sweeps.cc`             | Yes     |
| Modify `src/sweeps.h`              | No      |
| Modify `src/runner.{h,cc}`         | No      |
| Modify `src/aggregate.{h,cc}`      | No      |
| Modify `app/main.cc`               | No      |
| Add new source files               | No      |
| Modify evaluator files             | No      |
