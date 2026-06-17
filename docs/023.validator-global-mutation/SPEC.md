---
case_id: 023-validator-global-mutation
title: Submission Validator Global Mutation 
primary_dimension: side_effect_isolation
secondary_dimensions:
  - testability
language: C++
difficulty: easy-medium
loc: ~150
---

## Problem Context
A student submission grading app processes assignments and tracks how many submissions were successfully validated. A `Reporter` class reads a global counter `total_processed` at the end of a run to print a summary. A `Grader` class grades individual submissions and does not touch the global counter. 

The product now needs a `Validator` class that checks whether a submission is eligible for grading (not empty and not late).

The design pressure is maintainability:
- keep validation logic free of side effects 
- preserve the global counter as something only the caller updates 
- keep the validator independently testable 

## Given Code
Starter code provides:
- `src/stats.h` / `.cc` with global counter: `int total_processed` 
- `src/grader.h` / `.cc` with grading logic (does not touch stats)
- `src/reporter.h` / `.cc` that reads `total_processed` for summary 
- `src/validator.h` / `.cc` with a stubbed `Validator::validate` implementation
- `app/main.cc` entrypoint
- evaluator tests and a structural side-effect check

Initial state compiles, but tests fail because `Validator::validate` is currently a stub.

## Agent-Facing Contract (This Text Must Match TASK.md)

### Task

The grading app needs a new `Validator` class that checks whether a submission is eligible for grading.

Complete the existing `Validator` class by implementing a method named `validate` that accepts a `Submission` and returns `true` if the submission is eligible and `false` otherwise.

### Requirements

- Return `false` if the submission content is empty.
- Return `false` if the submission is marked late (`s.is_late == true`).
- Return `true` otherwise.

### Constraints

- Do not add external dependencies.
- Do not modify `app/main.cc`.
- Do not modify files under `evaluator`.
- You may add or modify files under `src`.
- The project must compile and all existing tests must pass after the change.

## Expected Design Direction (Human-Facing)
`Validator` only inspects the submission and returns a boolean. It does not touch `total_processed` or include `stats.h` at all. 

The caller (`main.cc`) is the right place to increment `total_processed` after a successful validation. The validator should not know or care that a counter exists.

Recommended shape:
- keep validation logic in `Validator`
- do not reference `total_processed` or include `stats.h` inside `Validator`
- increment `total_processed` in caller code (`main.cc`), not inside core validation logic

Acceptable approaches:
- `Validator` class with a side-effect free `validate()` method.

This case does not require one exact layout beyond providing a `Validator` class with a compatible `validate()` method.

## Hidden Evaluator Intent
Primary maintainability probe:
- D9 Side-Effect Isolation

The evaluator rewards:
- correct true/false outcomes for empty, late, and valid submissions
- `Validator` logic that does not reference `total_processed`
- `Validator` that does not include `stats.h`

The evaluator penalizes:
- any reference to `total_processed` inside `validator.h` or `validator.cc`
- including `stats.h` in validator files
- modifying `reporter.cc` or `grader.cc` to compensate for wrong counter value

## Evaluation Criteria

### Functional
- `validate()` returns false for empty submissions
- `validate()` returns false for late submissions
- `validate()` returns true for valid submissions
- `total_processed` reflects the correct count after all submissions are processed

### Structural
- enforced by `evaluator/023.validator-global-mutation/pipeline.json`
  using `baseline_diff` and `source_analysis` modules
- `validator.h` / `validator.cc` must not reference `total_processed`
- `validator.h` / `validator.cc` must not include `stats.h`
- `app/main.cc`, `reporter.cc`, and `grader.cc` must not be modified

### Maintainability
- validation logic is side-effect free
- global counter ownership stays with the caller
- validator is independently testable without any global state

## Oracle Signals
- C++ functional tests verify `validate()` return values
- Python functional tests verify the processed count
- structural check catches any forbidden `total_processed` / `stats.h` usage outside the allowed ownership files
- `app/main.cc`, `reporter.cc`, and `grader.cc` are not modified by the agent 
- `total_processed` is only incremented in `main.cc`

## Common Failure Modes (Non-Scoring)
- including `stats.h` in `validator.cc` or `validator.h`
- incrementing `total_processed` inside `validate()`
- modifying `reporter.cc` to compensate for wrong counter value
- modifying `grader.cc` to call validate() internally
- editing evaluator tests or checks 

## Distinctness and Mapping
Primary Dimension:
- D9 Side-Effect Isolation

Measured Capability:
- keep core logic free of global state mutation
- preserve single ownership of shared counters

Secondary Dimensions:
- D7 Testability and Determinism (non-scoring support)

Why this case is different from similar cases:
- Case `010.logging-side-effects` tests output side effects (logging/printing inside core logic), which don't affect what other components compute. This case, `023.validator-global-mutation`, tests mutation side effects like modifying a global counter that directly affects what `Reporter` computes and prints. These are fundamentally different categories of side effects. 
- Case `019.ranking-explainability-boundary` (D9 multi-step) covers a situation where side effects may occur across multiple steps, while `023.validator-global-mutation` is a small, focused side-effect check that tests a situation where a single increment changes what another component reports. 

## Allowed & Disallowed Summary
| Action | Allowed |
|---|---|
| Add new files | Yes |
| Modify existing tests | No (evaluator-owned) |
| Add new dependencies | No |
| Modify `app/main.cc` | No |
| Use global mutable state in Validator | No |
