# How to Create a New Case

This document describes the recommended workflow for adding a new NITR case to this repository.

The repository-level convention is:

- starter code and agent-facing task live under `cases/<case-slug>/`
- human-facing case specification lives under `docs/<case-slug>/SPEC.md`
- evaluator code lives under `evaluator/<case-slug>/`

Note that [`docs/needle_in_the_repo_case_template.md`](docs/needle_in_the_repo_case_template.md) is the authoring template, but the current repository stores `SPEC.md` under `docs/`, not under `cases/`.

## 1. Pick a design dimension

Start by reading [`docs/design_matrix.md`](docs/design_matrix.md) and choose one primary design dimension from `D1` to `D9`.

When choosing the dimension:

- every case should have exactly one primary dimension
- the new case should fill a meaningful gap or strengthen existing coverage
- the task should stay narrow enough that the maintainability pressure is diagnosable

Before writing the case, decide:

- case id: use the next available three-digit prefix
- case slug: `<case-id>.<short-kebab-name>`
- whether the case is micro or multi-step

Example:

```text
022.example-case-name
```

## 2. Write `SPEC.md` from the template

Use [`docs/needle_in_the_repo_case_template.md`](docs/needle_in_the_repo_case_template.md) as the source template and create:

```text
docs/<case-slug>/SPEC.md
```

`SPEC.md` should:

- include the required metadata block
- state the problem context and given code
- include the full agent-facing task text
- describe expected design direction, evaluation criteria, oracle signals, and failure modes
- map the case back to the chosen design dimension

Important repository convention:

- `TASK.md` must be a strict subset of `SPEC.md`
- `SPEC.md` is stored in `docs/<case-slug>/SPEC.md`
- all documentation and code should remain in English even if contributor notes are written in another language

## 3. Add the new case under `cases/`

Create the new case directory:

```text
cases/<case-slug>/
```

At minimum, add:

```text
cases/<case-slug>/
|-- CMakeLists.txt
|-- TASK.md
|-- app/
|   `-- main.cc
`-- src/
```

Required work in this step:

- write the starter source code under `src/` and `app/`
- write `TASK.md` based on the task section from `SPEC.md`
- keep the starter repository small, targeted, and compilable when possible
- make sure the task reads like a normal engineering request and does not expose evaluator intent

If the case is multi-step, add `TASK1.md`, `TASK2.md`, and so on following the existing repository style.

You also need to register the new case in [`cases/CMakeLists.txt`](cases/CMakeLists.txt) so it can be configured and built.

## 4. Add the evaluator under `evaluator/`

Create:

```text
evaluator/<case-slug>/
|-- checks/
|-- data/
`-- tests/
```

The evaluator should usually include:

- functional unit tests under `tests/`
- structural or maintainability checks under `checks/`
- fixtures or golden files under `data/` when needed

Typical evaluator patterns already used in this repository:

- C++ tests for behavior verification
- Python scripts for structure or policy checks
- lightweight fixture files for parity or oracle comparisons

You also need to register the new evaluator in [`evaluator/CMakeLists.txt`](evaluator/CMakeLists.txt) by:

- adding a `nitr_register_case_<id>()` function or equivalent block
- wiring the test targets and Python checks
- adding the new case to `nitr_add_evaluator(...)`

## 5. Validate locally

Before opening a pull request, validate the new case locally.

Typical commands:

```bash
cmake -S . -B build \
  -DNITR_BUILD_ALL_CASES=OFF \
  -DNITR_CASE=<case-slug> \
  -DNITR_BUILD_EVALUATOR=ON

cmake --build build

ctest --test-dir build --output-on-failure

python3 tools/run_case.py <case-slug>
python3 tools/run_case.py <case-slug> --with-evaluator
python3 tools/check_benchmark_consistency.py
python3 tools/check_evaluator_entrypoints.py
```

Recommended checks before submission:

- the new case configures successfully
- the evaluator runs successfully
- the repository-wide consistency checker does not report missing evaluator wiring
- the evaluator entrypoint checker does not report missing case-level CTest registration
- `TASK.md` does not leak the benchmark intent
- the case still isolates one primary maintainability pressure
- the naming and directory layout match existing cases

## 6. Open a pull request and merge to `main`

After local validation:

1. commit the new case, evaluator, and docs
2. open a pull request against `main`
3. include a short PR summary covering the chosen design dimension, the case goal, and evaluator strategy
4. address review comments
5. merge the PR into `main`

## Checklist

- [ ] Read [`docs/design_matrix.md`](docs/design_matrix.md) and pick one primary dimension
- [ ] Create `docs/<case-slug>/SPEC.md`
- [ ] Create `cases/<case-slug>/` with starter code and `TASK.md`
- [ ] Create `evaluator/<case-slug>/` with tests and structural checks
- [ ] Register the case in [`cases/CMakeLists.txt`](cases/CMakeLists.txt)
- [ ] Register the evaluator in [`evaluator/CMakeLists.txt`](evaluator/CMakeLists.txt)
- [ ] Run local build and evaluator checks
- [ ] Open PR and merge to `main`
