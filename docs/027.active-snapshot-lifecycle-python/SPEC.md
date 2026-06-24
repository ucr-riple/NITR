---
case_id: 027-active-snapshot-lifecycle-python
title: Active Snapshot Lifecycle, Python
primary_dimension: state_lifecycle
secondary_dimensions:
  - change_locality
  - testability
language: Python
granularity: multi-step
paired_with: 017.active-snapshot-lifecycle
difficulty: medium
loc: 200-300
---

# Case 027: Active Snapshot Lifecycle, Python

## Problem context

A small in-memory service answers key lookups from a currently active snapshot. Product requirements now need explicit lifecycle control over which snapshot is active at runtime. The system must support registering snapshots, switching the active snapshot, and clearing active state. Query behavior must remain deterministic across lifecycle transitions. The case is intentionally compact and excludes infra concerns.

## Case metadata and matrix rationale

- Case id / slug: `027-active-snapshot-lifecycle-python`
- Title: `Active Snapshot Lifecycle, Python`
- Primary dimension: `D8 State Ownership and Lifecycle`
- Secondary dimensions: `D1 Change Locality`, `D7 Testability and Determinism`
- Granularity: `multi-step`
- Paired with: `017.active-snapshot-lifecycle`
- Difficulty: `medium`

Rationale for inclusion:

- This case is a Python paired port of case `017.active-snapshot-lifecycle`.
- It preserves the same ownership and lifecycle probe while validating whether the benchmark's state-lifecycle signals remain robust across languages.
- The central question is unchanged: when active snapshot lifecycle requirements grow, does mutable active-state ownership remain localized, or do stale references and parallel trackers spread across the codebase?

## Given code

The starter repository should run successfully and all provided tests should pass. The initial code should remain small and centered on one in-memory snapshot subsystem.

Expected starter shape:

```text
- cases/027.active-snapshot-lifecycle-python/app/main.py
- cases/027.active-snapshot-lifecycle-python/src/snapshot.py
- cases/027.active-snapshot-lifecycle-python/src/query_result.py
- cases/027.active-snapshot-lifecycle-python/src/snapshot_store.py
- cases/027.active-snapshot-lifecycle-python/src/query_service.py
- cases/027.active-snapshot-lifecycle-python/TASK1.md
- cases/027.active-snapshot-lifecycle-python/TASK2.md
- cases/027.active-snapshot-lifecycle-python/TASK3.md
- cases/027.active-snapshot-lifecycle-python/CMakeLists.txt
- evaluator/027.active-snapshot-lifecycle-python/pipeline.json
- evaluator/027.active-snapshot-lifecycle-python/data
- evaluator/027.active-snapshot-lifecycle-python/tests
- docs/027.active-snapshot-lifecycle-python/SPEC.md
```

Starter design assumptions:

- snapshot domain data includes a version id and key-value payload
- a store/registry owns registered snapshots and resolves the currently active snapshot
- a query service is used by `app/main.py`
- the baseline includes an active-snapshot concept, but lifecycle behavior is incomplete or under-specified
- the Python starter should expose room for stale aliasing or duplicated active-state tracking if extended poorly

The starter code should make the lifecycle ownership boundary discoverable through normal repository reading, but it should not already satisfy the full multi-step lifecycle contract.

## Agent-facing contract

The following sections are the full text of `TASK1.md`, `TASK2.md`, and `TASK3.md`. The internal sections that follow are not exposed to the coding agent.

# Task 1

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

# Task 2

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

# Task 3

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

## Expected design direction (human-facing)

Acceptable solution directions:

- keep lifecycle mutation responsibility concentrated in one core owner component
- keep query path read-focused and dependent on current active snapshot resolution
- the query service should resolve the active snapshot through the lifecycle owner when answering queries, rather than retaining a writable or stale active snapshot alias
- keep public API additions narrow and directly tied to lifecycle requirements

Undesirable directions:

- proliferating active-state mutation across unrelated modules
- storing parallel writable active-version trackers in multiple classes or modules
- letting the query layer keep stale mutable snapshot aliases across replacement or reset
- shifting lifecycle logic into demo wiring code

## Hidden evaluator intent

This is a D8 multi-step case. The maintainability signal is whether mutable active-state ownership remains explicit and localized as the lifecycle grows from registration/activation to replacement and reset.

The case is intentionally about lifecycle ownership, not infrastructure:

- no persistence
- no background refresh
- no concurrency
- no external loading

The core question is whether the implementation keeps one authoritative owner for active snapshot state and resolves queries from that authority, or whether query code and helper layers accumulate stale aliases, partial reset rules, or duplicate trackers.

Registration should not allow later caller-side mutation of the original payload object to silently change the registered snapshot. A registered snapshot should own a stable in-memory snapshot of the provided payload.

## Functional expectations

The finished implementation should support:

- duplicate snapshot registration rejection
- activation of registered snapshots
- failed activation for unknown versions without changing the current active snapshot
- replacement semantics where queries observe only the newly active snapshot
- reset semantics where no active snapshot produces `kNoActiveSnapshot`
- repeated transitions:
  - `v1 -> v2 -> v3`
  - `vX -> reset -> vY`

Expected query contract:

- active snapshot exists and key exists: `kFound` with value
- active snapshot exists and key missing: `kNotFound` with no value
- no active snapshot: `kNoActiveSnapshot` with no value

After replacement and after reset, queries must not return stale data from previously active snapshots.

## Evaluator plan

### Functional checks

The evaluator should add or run tests for:

- baseline active query behavior
- duplicate registration rejection
- activating a known snapshot
- failed activation of an unknown snapshot while keeping the previous active snapshot
- replacement sequences (`v1 -> v2 -> v3`)
- reset behavior (`kNoActiveSnapshot`)
- reset-then-reactivate behavior
- stale snapshot isolation after replacement and reset

### Structural / oracle checks

Recommended checks:

- reject namespace/module-level mutable active-state globals
- reject multiple writable active-state trackers across core ownership modules
- reject query-layer ownership of mutable snapshot payload or active snapshot aliases
- reject lifecycle mutation logic in `app/main.py`
- reject reset ownership logic outside the intended lifecycle owner

These checks should remain secondary to functional sequence tests. They are meant to catch obvious ownership drift, not force one exact class or module layout.

## Failure modes (non-scoring)

- duplicated active-version or active-snapshot trackers
- stale snapshot aliases surviving replacement
- reset implemented as partial flags without clearing authoritative active state
- query layer caching mutable snapshot payload instead of resolving from the active owner
- lifecycle mutation logic spread across query and demo layers

## Maintainability mapping

Primary Dimension:
- D8 State Ownership and Lifecycle

Measured Capability:
- localizing mutable active-state ownership
- keeping replace/reset invalidation semantics coherent over time

Secondary Dimensions:
- D1 Change Locality
- D7 Testability and Determinism

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new files under `src/` | Yes |
| Modify existing core logic | Yes |
| Modify existing tests | Yes, only to add lifecycle coverage |
| Add new dependencies | No |
| Modify public modules/APIs | Yes, if required by lifecycle API |
| Use global mutable state | No |
| Introduce new external IO | No |
