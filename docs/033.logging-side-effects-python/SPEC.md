---
case_id: 033-logging-side-effects-python
title: Logging Side Effects, Python
primary_dimension: side_effect_isolation
secondary_dimensions: []
language: Python
granularity: micro
paired_with: 010.logging-side-effects
difficulty: easy
loc: ~80-140
---

# Case 033: Logging Side Effects, Python

## Problem context

A loan review workflow evaluates applicants with three deterministic policy
rules. Batch review must now emit an audit message for every applicant while
also returning approved applicant ids.

## Case metadata and matrix rationale

- Case id / slug: `033-logging-side-effects-python`
- Title: `Logging Side Effects, Python`
- Primary dimension: `D9 Side-Effect Isolation`
- Secondary dimensions: none
- Granularity: `micro`
- Paired with: `010.logging-side-effects`
- Difficulty: `easy`

This is a Python paired port of case `010.logging-side-effects`. It preserves
the functional contract and D9 probe while replacing C++ header/signature
inspection with Python AST analysis.

## Given code

Expected starter shape:

```text
- cases/033.logging-side-effects-python/app/main.py
- cases/033.logging-side-effects-python/src/applicant.py
- cases/033.logging-side-effects-python/src/audit_logger.py
- cases/033.logging-side-effects-python/src/loan_policy.py
- cases/033.logging-side-effects-python/src/loan_review_service.py
- cases/033.logging-side-effects-python/TASK.md
- evaluator/033.logging-side-effects-python/tests/test_loan_review.py
- evaluator/033.logging-side-effects-python/checks/run_evaluator.py
```

The starter policy returns a default denial decision. The batch service already
calls the policy but emits only a placeholder audit message.

## Agent-facing contract

The following section is the full text of `TASK.md`. The internal sections that
follow are not exposed to the coding agent.

## Task

Implement the loan review workflow in `src/`.

### Requirements

- `evaluate_applicant()` should determine whether an applicant is approved and
  list denial reasons.
- `review_applicants()` should process a batch of applicants, return approved
  applicant ids in input order, and emit one audit log line per applicant.
- Approval rules:
  - credit score must be at least `700`
  - annual income must be at least `50000`
  - debt ratio must be at most `0.40`
- Use the exact denial reason tokens in this order:
  1. `low_credit`
  2. `low_income`
  3. `high_debt`
- Use the exact audit message format:
  - approved applicant: `"<id> approved"`
  - denied applicant: `"<id> denied: <reason1>,<reason2>,..."`

### Constraints

- Keep the existing public classes and function names unchanged.
- Keep applicant evaluation independent of audit logging and direct I/O.
- Implement the change in files under `src/` and do not add external
  dependencies.

## Expected design direction (human-facing)

- `evaluate_applicant()` computes and returns a `ReviewDecision` without I/O.
- `review_applicants()` owns the audit message formatting and logger call.
- `AuditLogger` remains substitutable so functional tests can inject an
  in-memory implementation.

## Hidden evaluator intent

Primary maintainability probe:

- D9 Side-Effect Isolation

The evaluator verifies functional behavior and uses AST analysis to ensure
that `loan_policy.py` does not import logging infrastructure, accept a logging
dependency, or directly perform logging/I/O. It also verifies that audit
emission remains localized in `loan_review_service.py`.

## Functional expectations

- exact threshold behavior at `700`, `50000`, and `0.40`
- ordered denial tokens
- approved ids retain input order
- exactly one correctly formatted audit message per applicant
- a missing logger disables audit output without changing review behavior

## Evaluator plan

### Functional checks

The evaluator runs tests for:

- approval of an eligible applicant
- rejection with all denial reasons in the required order
- inclusive behavior at the three approval thresholds
- approved applicant ids in input order
- one exact audit message per applicant
- review behavior when no logger is supplied

The starter is intentionally incomplete and should fail these functional
checks until the task is implemented.

### Structural / oracle checks

The AST-based evaluator checks that:

- `loan_policy.py` does not import `audit_logger` or Python's `logging` module
- `evaluate_applicant()` accepts only the applicant dependency
- policy code does not call direct I/O functions such as `print()` or `open()`
- policy code does not call logger methods
- `loan_review_service.py` owns the `logger.log()` call

These checks distinguish a behaviorally correct implementation with localized
side effects from one that couples policy evaluation to audit infrastructure.

## Failure modes (non-scoring)

- injecting an audit logger into `evaluate_applicant()`
- importing audit or logging infrastructure from `loan_policy.py`
- emitting audit messages directly from policy code
- using direct I/O such as `print()` or `open()` in policy code
- moving audit emission out of `review_applicants()` into the policy layer
- producing the correct decisions and messages while mixing calculation and
  side-effect responsibilities

## Maintainability mapping

Primary Dimension:

- D9 Side-Effect Isolation

Measured Capability:

- keep deterministic policy decisions independent of logging infrastructure
- localize audit message formatting and emission at the orchestration boundary

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new files under `src/` | Yes |
| Modify existing source files | Yes |
| Modify evaluator tests | No |
| Add external dependencies | No |
| Change existing public API | No |
| Log or perform direct I/O from policy code | No |
