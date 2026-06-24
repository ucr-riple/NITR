## Task

Extend the snapshot query subsystem so it supports explicit snapshot registration and activation.

### Requirements
- Add an in-memory snapshot registration API that accepts:
  - snapshot version id
  - key-value payload
- Duplicate snapshot registration for an existing version must be rejected.
- Add an activation API that sets a registered snapshot as the current active snapshot.
- Activating an unknown snapshot version must fail and keep the previously active snapshot unchanged.
- Query behavior must follow this contract exactly:
  - active snapshot exists and key exists: return `kFound` with value
  - active snapshot exists and key missing: return `kNotFound` with no value
  - no active snapshot: return `kNoActiveSnapshot` with no value

### Constraints
- Keep the system in-memory and deterministic.
- Do not introduce concurrency, threads, persistence, networking, or filesystem-based loading.
- Keep `app/main.py` as a small demo entry point.
- You may add files under `src/`.
- Do not remove existing behavior unless required by the lifecycle contract above.
