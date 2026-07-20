---
case_id: 036-stable-public-api-python
title: Stable Public API, Python
primary_dimension: change_locality
secondary_dimensions: []
language: Python
granularity: micro
paired_with: 013.stable-public-api
difficulty: easy
loc: ~60-120
---

# Case 036: Stable Public API, Python

## Problem context

A library catalog exposes title lookup and digest generation through a small
public service. Archived books must now be excluded from both outputs while
the behavior for visible books stays unchanged.

## Case metadata and matrix rationale

- Case id / slug: `036-stable-public-api-python`
- Title: `Stable Public API, Python`
- Primary dimension: `D1 Change Locality`
- Secondary dimensions: none
- Granularity: `micro`
- Paired with: `013.stable-public-api`
- Difficulty: `easy`

Rationale for inclusion:

- This case is a Python paired port of case `013.stable-public-api`.
- It preserves the same semantic-refinement versus public-API-churn probe.
- Python AST inspection replaces the C++ public-header signature oracle.

## Given code

Expected starter shape:

```text
- cases/036.stable-public-api-python/app/main.py
- cases/036.stable-public-api-python/src/library_catalog.py
- cases/036.stable-public-api-python/TASK.md
- cases/036.stable-public-api-python/CMakeLists.txt
- evaluator/036.stable-public-api-python/pipeline.json
- evaluator/036.stable-public-api-python/tests/test_catalog.py
- evaluator/036.stable-public-api-python/checks/run_evaluator.py
- evaluator/036.stable-public-api-python/data/README.md
- docs/036.stable-public-api-python/SPEC.md
```

The starter defines the complete public `Book` and `CatalogService` API.
Lookup sorting and digest formatting already work, but archived books are still
included in both outputs.

## Agent-facing contract

The following section is the full text of `TASK.md`. The internal sections that
follow are not exposed to the coding agent.

Implement the requested catalog behavior change.

Requirements:

- archived books must not appear in title lookup results
- archived books must not appear in the catalog digest
- keep the existing behavior for non-archived books

Do not modify the evaluator.

## Expected design direction (human-facing)

The archive rule should be implemented inside the existing catalog behavior.
The public `Book` fields and the two `CatalogService` methods already contain
all information required by the change and should remain stable.

No public mode flags, replacement methods, or callsite policy should be needed.

## Hidden evaluator intent

This is a D1 micro case. The signal is whether a small semantic refinement
remains local to the implementation or causes public signature and callsite
changes.

Functional tests invoke the established service directly, while AST checks
lock the public types and signatures to their starter shape.

## Functional expectations

- archived books never appear in prefix lookup results
- visible matching titles remain sorted
- archived books never appear in the digest
- visible digest rows preserve their existing formatting and input order
- an all-archived collection produces no matches and an empty digest body
- books whose `archived` argument is omitted remain visible

## Evaluator plan

### Functional checks

The evaluator tests:

- a prefix shared by archived and visible titles
- a prefix that matches only an archived title
- empty-prefix lookup ordering across all visible titles
- exact digest output with mixed visibility
- lookup and digest behavior for an all-archived collection
- the existing default value of `Book.archived`

### Structural / oracle checks

The AST evaluator checks that:

- `Book` retains exactly the public fields `id`, `title`, `author`, and
  `archived` in their existing order
- `CatalogService` retains exactly its two public methods
- `find_available_titles(self, books, prefix)` keeps its exact signature
- `build_catalog_digest(self, books)` keeps its exact signature
- no defaults, variadic parameters, or archive-control flags are added to the
  service boundary

Private implementation helpers remain allowed.

## Failure modes (non-scoring)

- adding `include_archived`, `show_archived`, or another public mode flag
- adding parameters or defaults to either established service method
- replacing the existing methods with new public entrypoints
- moving archive filtering to the application or external callsites
- changing the `Book` public data shape for an internal semantic refinement
- preserving visible behavior only for the sample input rather than arbitrary
  catalog collections

## Maintainability mapping

Primary Dimension:

- D1 Change Locality

Measured Capability:

- implement a semantic behavior change without widening public interfaces
- keep policy inside the component that already owns the behavior
- preserve established data and service contracts

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add private helpers | Yes |
| Modify catalog implementation behavior | Yes |
| Modify evaluator files | No |
| Add external dependencies | No |
| Change `Book` public fields | No |
| Change `CatalogService` public methods or signatures | No |
| Add public archive-control flags | No |
