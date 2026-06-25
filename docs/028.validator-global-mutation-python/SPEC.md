---
case_id: 028-validator-global-mutation-python
title: Submission Validator Global Mutation, Python
primary_dimension: side_effect_isolation
secondary_dimensions:
  - testability
language: Python
granularity: micro
paired_with: 023.validator-global-mutation
difficulty: easy-medium
loc: ~120-180
---

# Case 028: Submission Validator Global Mutation, Python

## Problem Context

A student submission grading app processes assignments and tracks how many submissions were successfully validated. A `Reporter` reads a global counter `total_processed` at the end of a run to print a summary. A `Grader` scores individual submissions and does not touch the global counter.

The product now needs a `Validator` that checks whether a submission is eligible for grading: it must not be empty and it must not be late.

The maintainability pressure is unchanged from case `023`:
- keep validation logic free of side effects
- preserve the global counter as something only the caller updates
- keep the validator independently testable

## Case metadata and matrix rationale

- Case id / slug: `028-validator-global-mutation-python`
- Title: `Submission Validator Global Mutation, Python`
- Primary dimension: `D9 Side-Effect Isolation`
- Secondary dimensions: `D7 Testability and Determinism`
- Granularity: `micro`
- Paired with: `023.validator-global-mutation`
- Difficulty: `easy-medium`

Rationale for inclusion:

- This case is a Python paired port of case `023.validator-global-mutation`.
- It preserves the same side-effect isolation probe while checking whether the benchmark can detect global-state contamination without relying on C++ include boundaries.
- The central question is unchanged: does validation remain a side-effect free predicate, or does it start mutating shared process-wide state?

## Given code

The starter repository should run successfully and all provided tests should pass once the stubbed validator behavior is completed.

Expected starter shape:

```text
- cases/028.validator-global-mutation-python/app/main.py
- cases/028.validator-global-mutation-python/src/submission.py
- cases/028.validator-global-mutation-python/src/validator.py
- cases/028.validator-global-mutation-python/src/grader.py
- cases/028.validator-global-mutation-python/src/reporter.py
- cases/028.validator-global-mutation-python/src/stats.py
- cases/028.validator-global-mutation-python/TASK.md
- cases/028.validator-global-mutation-python/CMakeLists.txt
- evaluator/028.validator-global-mutation-python/pipeline.json
- evaluator/028.validator-global-mutation-python/tests/test_validator.py
- evaluator/028.validator-global-mutation-python/checks/run_evaluator.py
- docs/028.validator-global-mutation-python/SPEC.md
```

Starter design assumptions:

- `stats.py` defines a module-level global counter `total_processed`
- `reporter.py` reads that counter to produce a summary string
- `grader.py` scores submissions without touching global state
- `validator.py` is the intended place for validation logic, but starts incomplete
- `app/main.py` owns the caller flow that validates, increments, grades, and prints

The Python starter should make the wrong move attractive: mutating `total_processed` inside `validator.py` or importing `stats` into validation code.

## Agent-facing contract

The following section is the full text of `TASK.md`. The internal sections that follow are not exposed to the coding agent.

## Task

The grading app needs a new `Validator` class that checks whether a submission is eligible for grading.

Complete the existing `Validator` class by implementing a method named `validate` that accepts a `Submission` and returns `True` if the submission is eligible and `False` otherwise.

### Requirements

- Return `False` if the submission content is empty.
- Return `False` if the submission is marked late (`submission.is_late is True`).
- Return `True` otherwise.

### Constraints

- Do not add external dependencies.
- Do not modify `app/main.py`.
- Do not modify files under `evaluator`.
- You may add or modify files under `src`.
- The project must run and all existing tests must pass after the change.

## Expected design direction (human-facing)

`Validator` only inspects the submission and returns a boolean. It does not read or mutate `total_processed`, and it does not depend on the stats module at all.

The caller (`app/main.py`) is the right place to increment `total_processed` after a successful validation. The validator should not know or care that a counter exists.

Recommended shape:

- keep validation logic in `Validator`
- do not reference `total_processed` inside `validator.py`
- do not import `stats` inside `validator.py`
- increment `total_processed` in caller code (`app/main.py`), not inside core validation logic

Acceptable approaches:

- a side-effect free `Validator.validate()` method

This case does not require one exact layout beyond providing a `Validator` class with a compatible `validate()` method.

## Hidden evaluator intent

Primary maintainability probe:

- D9 Side-Effect Isolation

The evaluator rewards:

- correct true/false outcomes for empty, late, and valid submissions
- `Validator` logic that does not reference `total_processed`
- `Validator` that does not import `stats`

The evaluator penalizes:

- any reference to `total_processed` inside `validator.py`
- importing `stats` inside `validator.py`
- modifying `reporter.py` or `grader.py` to compensate for wrong counter value

Calling `Validator.validate()` should not change `total_processed`, regardless of whether the submission is valid or invalid. Counter ownership should remain entirely outside validator logic.

## Functional expectations

The finished implementation should support:

- `validate()` returns `False` for empty submissions
- `validate()` returns `False` for late submissions
- `validate()` returns `True` for valid submissions
- calling `validate()` alone does not change `total_processed`
- `total_processed` reflects the correct count after all submissions are processed

## Structural / oracle checks

Recommended checks:

- `validator.py` must not reference `total_processed`
- `validator.py` must not import `stats`
- files other than `stats.py`, `reporter.py`, and `app/main.py` must not reference `total_processed`
- files other than `stats.py`, `reporter.py`, and `app/main.py` must not import `stats`
- `app/main.py`, `reporter.py`, and `grader.py` should remain protected starter-owned boundaries

These checks should remain secondary to functional correctness, but they are the core maintainability signal for the case.

## Common failure modes (non-scoring)

- importing `stats` in `validator.py`
- incrementing `total_processed` inside `validate()`
- modifying `reporter.py` to compensate for a wrong counter value
- modifying `grader.py` to call validation internally
- editing evaluator tests or checks

## Maintainability mapping

Primary Dimension:

- D9 Side-Effect Isolation

Measured Capability:

- keep core logic free of global state mutation
- preserve single ownership of shared counters

Secondary Dimensions:

- D7 Testability and Determinism

Why this case is different from similar cases:

- Case `010.logging-side-effects` tests output-side effects that do not directly change what peer components compute.
- This case tests mutation side effects: a single increment changes what `Reporter` computes and prints.
- Case `019.ranking-explainability-boundary` is the multi-step D9 probe; this case remains a compact, single-boundary D9 micro.

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new files | Yes |
| Modify existing tests | No (evaluator-owned) |
| Add new dependencies | No |
| Modify `app/main.py` | No |
| Use global mutable state in `Validator` | No |
