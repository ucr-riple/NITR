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

## Problem Context

A loan review workflow evaluates applicants with three deterministic policy
rules. Batch review must now emit an audit message for every applicant while
also returning approved applicant ids.

The design pressure is to keep the policy calculation pure and independent of
logging infrastructure. Audit emission belongs at the orchestration boundary,
where the policy decision is converted into a message. A behaviorally correct
solution that injects a logger into `evaluate_applicant()`, logs from policy
code, or performs direct I/O there fails the maintainability objective.

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

The full agent-facing contract is maintained in `TASK.md`. It requires the
three approval rules, ordered denial reasons, stable approved-id ordering, and
exact audit message formatting while preserving the public API.

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

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new files under `src/` | Yes |
| Modify existing source files | Yes |
| Modify evaluator tests | No |
| Add external dependencies | No |
| Change existing public API | No |
| Log or perform direct I/O from policy code | No |
