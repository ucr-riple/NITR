## Task

Add `sweep_warmup_x_lr` to `src/sweeps.cc`.

The sweep should search over a grid of warmup step counts and learning rates, producing a
`SweepResult` with one entry per `(warmup_steps, lr)` combination.

### Requirements

- Accept a base `TrialParams`, a `std::vector<int>` of warmup step counts, and a
  `std::vector<double>` of learning rates.
- Cover the full Cartesian product of the two grids.
- Populate `configs`, `results`, `best_idx`, and `summary` consistent with the conventions
  of the existing sweeps in `src/sweeps.cc`.

### Constraints

- Implement in `src/sweeps.cc` only.
- Do not modify `src/sweeps.h`, `app/main.cc`, or any file under `evaluator/`.
- Do not add new source files.
