### Task

The grading app needs a new `Validator` class that checks whether a submission is eligible for grading.

Add a `Validator` class with a method named `validate` that accepts a `Submission` and returns `true` if the submission is eligible and `false` otherwise.

### Requirements

- Return `false` if the submission content is empty.
- Return `false` if the submission is marked late (`s.is_late == true`).
- Return `true` otherwise.

### Constraints

- Do not add external dependencies.
- Do not modify `app/main.cc`.
- Do not modify files under `evaluator/023.validator-global-mutation/`.
- You may add or modify files under `cases/023.validator-global-mutation/src`.
- The project must compile and all existing tests must pass after the change.