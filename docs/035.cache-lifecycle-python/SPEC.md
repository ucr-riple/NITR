---
case_id: 035-cache-lifecycle-python
title: Cache Lifecycle, Python
primary_dimension: state_ownership_and_lifecycle
secondary_dimensions: []
language: Python
granularity: micro
paired_with: 012.cache-lifecycle
difficulty: easy-medium
loc: ~90-160
---

# Case 035: Cache Lifecycle, Python

## Problem context

An inventory report service stores products and delegates summary calculation
to a summary engine. It now needs to reuse summaries between unchanged reads
while refreshing them after product mutations or an explicit cache clear.

## Case metadata and matrix rationale

- Case id / slug: `035-cache-lifecycle-python`
- Title: `Cache Lifecycle, Python`
- Primary dimension: `D8 State Ownership and Lifecycle`
- Secondary dimensions: none
- Granularity: `micro`
- Paired with: `012.cache-lifecycle`
- Difficulty: `easy-medium`

Rationale for inclusion:

- This case is a Python paired port of case `012.cache-lifecycle`.
- It preserves the same ownership, invalidation, and reset lifecycle probe.
- Python AST checks replace C++ header and static-state inspection.

## Given code

Expected starter shape:

```text
- cases/035.cache-lifecycle-python/app/main.py
- cases/035.cache-lifecycle-python/src/product.py
- cases/035.cache-lifecycle-python/src/summary_engine.py
- cases/035.cache-lifecycle-python/src/inventory_report_service.py
- cases/035.cache-lifecycle-python/TASK.md
- cases/035.cache-lifecycle-python/CMakeLists.txt
- evaluator/035.cache-lifecycle-python/pipeline.json
- evaluator/035.cache-lifecycle-python/tests/test_report_cache.py
- evaluator/035.cache-lifecycle-python/checks/run_evaluator.py
- evaluator/035.cache-lifecycle-python/data/README.md
- docs/035.cache-lifecycle-python/SPEC.md
```

The starter service already owns its product collection and delegates every
summary request to a pure `SummaryEngine`. `clear_cache()` is present but has
no implementation, and repeated reads currently recompute.

## Agent-facing contract

The following section is the full text of `TASK.md`. The internal sections that
follow are not exposed to the coding agent.

# Task

Add summary caching to `InventoryReportService`.

Requirements:

- Repeated `get_summary()` calls should reuse the last computed summary when
  the product collection has not changed.
- `replace_products(...)` should make the old cached summary invalid.
- `upsert_product(...)` should make the old cached summary invalid.
- `clear_cache()` should force the next `get_summary()` call to recompute the
  summary.
- Keep the current behavior of summary values correct after product
  replacement and updates.

## Expected design direction (human-facing)

Cache state should belong to each `InventoryReportService` instance alongside
the products whose summary it represents. Product mutations and explicit
clearing should invalidate that local state. `SummaryEngine` should remain a
stateless computation dependency rather than becoming a cache owner.

The solution should preserve the existing public operations without adding
cache flags, refresh switches, keys, or inspection APIs.

## Hidden evaluator intent

This is a D8 micro case. The primary signal is whether mutable cache state has
one clear owner and a small, explicit set of invalidating lifecycle transitions.

The evaluator combines call-counting behavior with AST checks so a cache that
produces correct values but is shared globally, owned by the computation
engine, or controlled through expanded APIs does not satisfy the case.

## Functional expectations

- two unchanged reads invoke the engine only once
- replacement invalidates the previous summary
- updating an existing product invalidates the previous summary
- inserting a new product invalidates the previous summary
- `clear_cache()` forces exactly one new computation on the next read
- different service instances do not share cached values
- summary values remain correct throughout all transitions

## Evaluator plan

### Functional checks

The evaluator injects a counting summary engine and tests:

- repeated reads without mutation
- replacement after a populated cache
- update and insertion through `upsert_product()`
- explicit clearing after a populated cache
- independent summaries owned by two service instances

It checks both engine call counts and complete `InventorySummary` values.

### Structural / oracle checks

The AST evaluator checks that:

- `SummaryEngine` contains no cache-related state or cache semantics
- Python modules do not introduce module-level cache state
- classes do not introduce class-level shared cache state
- `InventoryReportService` still exposes `clear_cache()` and `get_summary()`
- service method signatures do not add cache-control parameters such as
  `use_cache`, `force_refresh`, `cache_key`, or `bypass_cache`
- `SummaryEngine` continues to expose the pure `compute()` seam

Instance-owned cache attributes inside `InventoryReportService` are allowed
and are the expected design direction.

## Failure modes (non-scoring)

- storing cached summaries on `SummaryEngine`
- using module-level or class-level cache state shared across services
- failing to invalidate after replacement, update, or insertion
- implementing `clear_cache()` without affecting the next read
- adding cache-control parameters to existing service methods
- exposing cache internals solely to make testing easier

## Maintainability mapping

Primary Dimension:

- D8 State Ownership and Lifecycle

Measured Capability:

- give mutable cache state one local owner
- keep invalidation and explicit reset transitions easy to identify
- preserve a stateless computation dependency and stable public API

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new files under `src/` | Yes |
| Modify existing source files | Yes |
| Modify evaluator files | No |
| Add external dependencies | No |
| Add service instance cache state | Yes |
| Add module-level or class-level shared cache state | No |
| Add cache-control parameters to public methods | No |
