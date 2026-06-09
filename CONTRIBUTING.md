# Contributing

## Scope

This repository accepts contributions that improve the NITR benchmark itself.
Typical contributions include:

- new benchmark cases under `cases/`, `docs/`, and `evaluator/`
- evaluator fixes or stronger public checks
- documentation improvements
- tooling improvements for local submission and evaluation

## Before You Change Code

- Read the top-level [`README.md`](README.md).
- For new benchmark cases, follow [`HOW_TO_CREATE_CASE.md`](HOW_TO_CREATE_CASE.md).
- For submit tooling changes, also check [`HOW_TO_SUBMIT.md`](HOW_TO_SUBMIT.md) and [`submit/README.md`](submit/README.md).
- Keep changes focused. Avoid mixing unrelated benchmark, evaluator, and tooling work in one pull request.

## Case Contributions

If you are adding a new case, the expected workflow is:

1. Choose a maintainability dimension from [`docs/design_matrix.md`](docs/design_matrix.md).
2. Write the case spec in `docs/<case-slug>/SPEC.md`.
3. Add the starter repository under `cases/<case-slug>/`.
4. Add the evaluator under `evaluator/<case-slug>/`.
5. Register the case in the relevant `CMakeLists.txt` files.
6. Update the root [`README.md`](README.md) if the public case count or case list changes.

## Build and Validation

At minimum, validate the affected case locally.

Example:

```bash
cmake -S . -B build \
  -DNITR_BUILD_ALL_CASES=OFF \
  -DNITR_CASE=022.as-of-eligibility-evaluation \
  -DNITR_BUILD_EVALUATOR=ON

cmake --build build
ctest --test-dir build --output-on-failure
```

If you change shared tooling or documentation, run the smallest relevant checks
that prove the change works.

If you add or modify evaluator files under `evaluator/`, also run:

```bash
python3 tools/check_benchmark_consistency.py
```

This script catches common public-evaluator wiring mistakes such as tests or
Python check scripts that exist on disk but are not covered by the repo-local
CTest path.

## Pull Requests

- Open a pull request against `main`.
- Describe the maintainability goal of the change, not just the surface behavior.
- For new cases, explain the primary dimension and how the evaluator distinguishes strong and weak solutions.
- If you add or rename files that affect documentation, update links in [`README.md`](README.md).

## Style Expectations

- Keep code and comments in English.
- Prefer small, explicit starter repositories over large or noisy examples.
- Keep evaluator checks narrow and explainable.
- Do not modify vendored third-party code unless the change is strictly necessary.
