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
