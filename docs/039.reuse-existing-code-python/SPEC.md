---
case_id: 039-reuse-existing-code-python
title: Reuse Existing Code, Python
primary_dimension: reuse
secondary_dimensions: []
language: Python
granularity: multi-step
paired_with: 003.reuse-existing-code
difficulty: easy
loc: ~70-130
---

# Case 039: Reuse Existing Code, Python

## Problem context

A numeric utility package already provides dot product and L2 norm operations.
A new cosine similarity function must handle invalid and zero-length inputs,
then combine the existing vector operations for valid sequences.

## Case metadata and matrix rationale

- Case id / slug: `039-reuse-existing-code-python`
- Title: `Reuse Existing Code, Python`
- Primary dimension: `D2 Reuse and Repo Awareness`
- Secondary dimensions: none
- Granularity: `multi-step`
- Paired with: `003.reuse-existing-code`
- Difficulty: `easy`

Rationale for inclusion:

- This case is a Python paired port of case `003.reuse-existing-code`.
- `std::span<const double>` becomes `Sequence[float]` while helper ownership is
  preserved.
- The evaluator combines AST call-path analysis with runtime helper spies so
  symbolic helper calls cannot hide a parallel implementation.

## Given code

Expected starter shape:

```text
- cases/039.reuse-existing-code-python/app/main.py
- cases/039.reuse-existing-code-python/src/dot_product.py
- cases/039.reuse-existing-code-python/src/l2_norm.py
- cases/039.reuse-existing-code-python/src/cosine_similarity.py
- cases/039.reuse-existing-code-python/TASK1.md
- cases/039.reuse-existing-code-python/TASK2.md
- cases/039.reuse-existing-code-python/TASK3.md
- cases/039.reuse-existing-code-python/CMakeLists.txt
- evaluator/039.reuse-existing-code-python/pipeline.json
- evaluator/039.reuse-existing-code-python/tests/test_cosine_similarity.py
- evaluator/039.reuse-existing-code-python/checks/run_evaluator.py
- docs/039.reuse-existing-code-python/SPEC.md
```

`dot_product()` and `l2_norm()` are complete existing utilities. The public
`cosine_similarity()` entrypoint is a placeholder, and only that source file
may change during the task.

## Agent-facing contract

The following sections reproduce the full texts of `TASK1.md`, `TASK2.md`, and
`TASK3.md`. Internal sections after them are not exposed to the coding agent.

## Task 1

## Task

Implement the basic input validation for
`cosine_similarity(a: Sequence[float], b: Sequence[float])` in
`src/cosine_similarity.py`.

### Requirements

- Raise `ValueError` when the two input sequences have different sizes.

### Constraints

- Keep the change localized to `src/cosine_similarity.py`.
- Do not modify other files under `src/`.
- Do not modify evaluator files.

## Task 2

## Task

Handle the zero-norm behavior for `cosine_similarity(...)` in
`src/cosine_similarity.py`.

### Requirements

- Keep the size-mismatch behavior working.
- Return `0.0` if either input vector has zero L2 norm.

### Constraints

- Reuse `l2_norm()` from `src/l2_norm.py`.
- Keep the change localized to `src/cosine_similarity.py`.
- Do not modify other files under `src/`.
- Do not modify evaluator files.

## Task 3

## Task

Finish `cosine_similarity(...)` in `src/cosine_similarity.py` using the
existing vector math helpers.

### Requirements

- Keep the size-mismatch and zero-norm behavior working.
- For non-zero valid inputs, return
  `dot_product(a, b) / (l2_norm(a) * l2_norm(b))`.

### Constraints

- Reuse `dot_product()` from `src/dot_product.py` and `l2_norm()` from
  `src/l2_norm.py`.
- Keep the change localized to `src/cosine_similarity.py`.
- Do not modify other files under `src/`.
- Do not re-implement dot product or L2 norm logic locally.
- Do not modify evaluator files.

## Expected design direction (human-facing)

`cosine_similarity()` should orchestrate three existing responsibilities:
input validation, norm-based zero handling, and composition of the shared dot
product and norm results. It should not own vector iteration or primitive math.

Direct imports, aliased imports, module-qualified calls, and small local
orchestration helpers are all acceptable.

## Hidden evaluator intent

This is a D2 multi-step case. The signal is whether the implementation discovers
and truly reuses both existing math authorities instead of duplicating their
logic while adding a higher-level function.

Static call detection alone is insufficient because an implementation can call
helpers and discard their results. A runtime spy check therefore replaces both
helper functions with sentinel-producing implementations before reloading the
cosine module.

## Functional expectations

- standard vectors produce the expected cosine similarity
- orthogonal vectors produce zero
- opposite-direction vectors produce a negative result
- mismatched sequence lengths raise `ValueError`
- zero and empty sequences produce zero
- arbitrary `Sequence[float]` implementations are accepted
- the result is derived from one dot-product result and two norm results

## Evaluator plan

### Functional checks

The evaluator tests numerical behavior across regular lists, tuples, and a
custom sequence implementation. It also tests mismatch and zero-norm behavior.

A dedicated helper-spy test patches `dot_product()` and `l2_norm()`, reloads
`cosine_similarity.py`, and supplies sentinel outputs whose composed result is
different from the mathematical cosine of the input. This proves the helper
outputs participate in the returned value.

### Structural / oracle checks

The AST evaluator:

- resolves direct, aliased, and module-qualified helper imports
- follows calls through local functions reachable from `cosine_similarity()`
- requires reachable calls to both `dot_product()` and `l2_norm()`
- rejects reachable manual loops
- rejects multiplication comprehensions that resemble copied vector math
- rejects direct square-root or hypotenuse primitives
- combines with a baseline diff that allows only `cosine_similarity.py` to
  change under `src/`

## Failure modes (non-scoring)

- reimplementing dot product with a loop or multiplication comprehension
- reimplementing L2 norm with `sqrt(sum(...))`
- adding renamed copies of the utilities inside `cosine_similarity.py`
- calling the helpers only to satisfy a static check and discarding the results
- modifying existing helpers instead of reusing them
- accepting only lists rather than the declared sequence boundary

## Maintainability mapping

Primary Dimension:

- D2 Reuse and Repo Awareness

Measured Capability:

- discover and reuse existing repository utilities
- keep primitive vector math centralized
- make a higher-level algorithm compose existing authorities

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Modify `src/cosine_similarity.py` | Yes |
| Modify other files under `src/` | No |
| Add new files | No |
| Modify evaluator files | No |
| Add external dependencies | No |
| Reuse `dot_product()` and `l2_norm()` | Yes |
| Reimplement vector math locally | No |
