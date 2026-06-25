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
