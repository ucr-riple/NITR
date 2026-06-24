## Task

Extend the snapshot lifecycle so the active snapshot can be replaced safely.

### Requirements
- Keep registration and activation behavior working.
- Support replacing the current active snapshot by activating a different registered snapshot.
- After replacement, queries must read only from the newly active snapshot.
- Repeated replace-after-replace transitions (`v1 -> v2 -> v3`) must work correctly.

### Constraints
- Keep the system in-memory and deterministic.
- Do not introduce concurrency, threads, persistence, networking, or filesystem-based loading.
- Keep `app/main.py` as a small demo entry point.
- You may add files under `src/`.
- Do not remove existing behavior unless required by the lifecycle contract above.
