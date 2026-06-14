# 010. logging-side-effects

## Summary
- **Project:** Needle in the Repo
- **Case ID:** 010
- **Case Name:** logging-side-effects
- **Primary maintainability dimension:** side_effect_containment
- **Secondary dimensions:** responsibility_separation, change_locality
- **Language:** C++
- **Difficulty:** easy

## Motivation
This case measures whether an agent can add an audit logging requirement without scattering side effects into core policy logic.

The desired implementation keeps the approval policy pure and localizes logging in the orchestration layer. A weak implementation may still pass the basic behavior tests while mixing `std::cout`, file writes, or logger calls into the rule evaluation code, which makes the code harder to extend and test.

## Human-facing task
Implement a small loan review workflow.

Each `Applicant` is reviewed against three approval rules:
- credit score must be at least `700`
- annual income must be at least `50000`
- debt ratio must be at most `0.40`

The workflow should:
1. evaluate each applicant,
2. collect the approved applicant ids in order,
3. emit one audit log line per applicant.

### Expected audit format
- Approved applicant: `"<id> approved"`
- Denied applicant: `"<id> denied: <reason1>,<reason2>,..."`

Use these reason tokens exactly:
- `low_credit`
- `low_income`
- `high_debt`

If an applicant violates multiple rules, list reasons in this exact order:
1. `low_credit`
2. `low_income`
3. `high_debt`

## TASK.md section
Implement the loan review workflow in `src/`.

Requirements:
- `EvaluateApplicant` should determine whether an applicant is approved and list denial reasons.
- `ReviewApplicants` should process a batch of applicants, return approved applicant ids in input order, and emit one audit log line per applicant.
- Keep all public headers and function names unchanged.
- The project should build with CMake and pass the provided tests.

## Maintainability intent
This case is designed to distinguish:
- adding a cross-cutting logging requirement while preserving clean boundaries,
from
- solving the task by injecting side effects into policy code.

Good solutions usually:
- keep `EvaluateApplicant` pure,
- keep logging in `ReviewApplicants` or another orchestration layer,
- reuse the existing `AuditLogger` abstraction rather than printing directly.

Risky solutions often:
- add logger parameters to core policy functions,
- print directly from `loan_policy.cc`,
- mix formatting and policy evaluation in the same function.

## Oracle signals
### Functional oracles
- approval decisions are correct
- denial reasons are correct and ordered
- approved ids preserve input order
- audit messages exactly match the required format

### Structural / maintainability oracles
- `loan_policy.h` / `loan_policy.cc` must not depend on `AuditLogger`
- `EvaluateApplicant` must not accept a logger parameter
- `loan_policy.cc` must not perform direct IO such as `std::cout`, `std::cerr`, `printf`, or file writes
- audit emission should be localized outside the policy function

## Expected file structure
- `cases/010.logging-side-effects/app/main.cc`
- `cases/010.logging-side-effects/src/`
- `cases/010.logging-side-effects/TASK.md`
- `cases/010.logging-side-effects/CMakeLists.txt`
- `evaluator/010.logging-side-effects/checks/maintainability_check.py`
- `evaluator/010.logging-side-effects/data/`
- `evaluator/010.logging-side-effects/tests/test_loan_review.cc`
- `docs/010.logging-side-effects/SPEC.md`
