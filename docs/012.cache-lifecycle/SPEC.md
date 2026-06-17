# 012. cache-lifecycle

## Summary
This case probes **state ownership and lifecycle** under a small performance-oriented change.
The task asks the agent to add summary caching to a report service so repeated reads avoid recomputation, while keeping cache ownership local, invalidation rules clear, and reset behavior explicit.

## Primary maintainability dimension
- **State Ownership and Lifecycle**

## Secondary dimensions
- API stability
- local reasoning over mutable state
- change locality

## Why this case exists
Coding agents often implement caching as a shortcut rather than as a maintainable state transition.
Common bad solutions include hidden shared mutable state, cache ownership in the wrong module, scattered invalidation logic, or public API pollution introduced only to manage cache behavior.
This case checks whether the agent can add a local optimization without making state boundaries harder to reason about.

## Repository structure
- `src/product.h`: product record used by the report service
- `src/summary_engine.h/.cc`: pure summary computation dependency
- `src/inventory_report_service.h/.cc`: service that owns products and should own cache state
- `app/main.cc`: demo executable
- `evaluator/012.cache-lifecycle/tests/test_report_cache.cc`: functional tests
- `evaluator/012.cache-lifecycle/pipeline.json`: structural and test pipeline

## Task intent
The service currently recomputes a summary on every read.
The requested change is to cache the latest summary and reuse it when the underlying product collection has not changed.
When products are replaced, updated, or explicitly reset, the cached summary must no longer be reused.

## Expected good solution shape
A good solution should:
- keep cache state inside `InventoryReportService`
- reuse the cached summary only when the product collection is unchanged
- invalidate cache in a small number of obvious lifecycle transitions
- keep `SummaryEngine` focused on pure summary computation
- avoid new public API knobs whose only purpose is cache management, except the requested `ClearCache()` method

## Common bad solutions
Bad solutions include:
- moving cache state into `SummaryEngine`
- introducing global or static cached summaries shared across instances
- scattering invalidation logic across unrelated helpers
- adding `use_cache`, `force_refresh`, cache-key parameters, or similar API churn to unrelated methods
- exposing internal cache state only for tests

## Functional requirements
1. `GetSummary()` should reuse the cached summary when no products have changed since the previous summary computation.
2. `ReplaceProducts(...)` should invalidate any previously cached summary.
3. `UpsertProduct(...)` should invalidate any previously cached summary.
4. `ClearCache()` should explicitly drop the cached summary so the next `GetSummary()` recomputes it.
5. Returned summaries must remain correct after replacement, update, and cache reset.

## Oracle signals
### Functional oracle
- repeated `GetSummary()` calls without mutations should trigger computation exactly once
- replacing products should force the next `GetSummary()` to recompute
- updating one product should force recomputation and return the new summary
- calling `ClearCache()` should force recomputation on the next read

### Structural oracle
- cache ownership should remain in `InventoryReportService`, not `SummaryEngine`
- `SummaryEngine` should remain a computation dependency, not a mutable cache owner
- no global or static cached summary should be introduced
- public APIs should not grow extra cache-control parameters beyond the requested `ClearCache()` method

## Evaluation focus
This case is not about whether caching exists in any form.
It is about whether the new mutable state is **owned locally, invalidated clearly, and lifecycle-managed without leaking across boundaries**.
