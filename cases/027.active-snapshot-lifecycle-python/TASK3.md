## Task

Finish the snapshot lifecycle by adding reset behavior and ensuring lifecycle transitions do not leave stale data behind.

### Requirements
- Keep registration, activation, and replacement behavior working.
- Add a reset API that clears the current active snapshot.
- Reset when already empty must be a no-op.
- After reset, queries must not return stale data from any previously active snapshot.
- Repeated reset-then-reactivate transitions (`vX -> reset -> vY`) must work correctly.

### Constraints
- Keep the system in-memory and deterministic.
- Do not introduce concurrency, threads, persistence, networking, or filesystem-based loading.
- Keep `app/main.py` as a small demo entry point.
- You may add files under `src/`.
- Do not remove existing behavior unless required by the lifecycle contract above.
