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