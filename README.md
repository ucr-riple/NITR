# Needle in the Repo: A Benchmark for Maintainability in AI-Generated Repository Edits
Haichao Zhu*, Qian Zhang*, Jiyuan Wang, Zhaorui Yang, and Yuxin Qiu (* indicates equal contribution)
<br>
| [arXiv](https://arxiv.org/abs/2603.27745) | [Project Page](https://www.cs.ucr.edu/~qzhang/nitr.html) |

TL;DR: Needle in the Repo (NITR) is a repository-level benchmark for evaluating whether
AI-generated repository edits preserve maintainable structure, not just
behavioral correctness. It comprises curated repository probes across
nine maintainability dimensions, pairing natural multi-file change requests
with hidden functional tests and structural oracles. The benchmark is designed
to expose cases where an agent produces behaviorally correct code that still
introduces maintainability failures such as weak modularity, poor testability,
or architectural shortcutting.

<p>
  <img src="logo/ucr.png" alt="UC Riverside logo" height="72">
  <img src="logo/tulane.png" alt="Tulane University logo" height="72">
</p>

![Pass/fail heatmap of 23 evaluated configurations across 21 cases.](docs/result_heatmap.png)

*Figure: Pass/fail heatmap of 23 evaluated configurations across 21 cases from the paper.*

Latest result matrix: [docs/model_case_pass_matrix.csv](docs/model_case_pass_matrix.csv)

## Overview

This repository contains the public benchmark release:

- starter cases under `cases/`
- case specifications and design docs under `docs/`
- public evaluator code under `evaluator/`
- agent-facing task statements (`TASK.md`, `TASK1.md`, ...)
- vendored dependencies required to build cases and evaluators

The current suite is predominantly C++, with Python pilot coverage beginning at
`026.inline-filter-entrypoint-reuse-python`.

This repository includes local submission helpers under `submit/` for
benchmark automation, but it does not include a hosted submission service.

## Repository Layout

```text
.
|-- cases/
|-- docs/
|-- evaluator/
|-- third_party/
|   |-- googletest/
|   |-- eigen3/
|   `-- json/
|-- CMakeLists.txt
`-- .gitignore
```

Each case directory contains starter source code plus one or more task files.
Multi-step cases use `TASK1.md`, `TASK2.md`, and `TASK3.md`. Single-step cases
use `TASK.md`. The `docs/` directory contains case specifications and
supporting benchmark design materials. The `evaluator/` directory contains the
public checks, tests, and fixtures used by this repository.

## How to Create a New Case

If you want to add a new NITR case to this repository, see
[`HOW_TO_CREATE_CASE.md`](HOW_TO_CREATE_CASE.md). It describes how to choose a
design dimension, write `SPEC.md` and `TASK.md`, add starter code under
`cases/`, add evaluator tests and structural checks under `evaluator/`, and
prepare the pull request to merge the new case into `main`.

## Submit Tooling

Local submission helpers now live under [`submit/README.md`](submit/README.md).
They can run cases against supported model backends, materialize generated case
directories, and run both submit and evaluator workflows locally or in the
pinned Linux/GCC Docker environment.

For an end-to-end usage guide, including single-case submit, batch submit, and
local evaluation, see [`HOW_TO_SUBMIT.md`](HOW_TO_SUBMIT.md).
Python package setup for the submit tooling is documented there as well.

## Build

Configure all cases:

```bash
cmake -S . -B build
```

Run the repository-wide C/C++ formatting check:

```bash
cmake -S . -B build
ctest --test-dir build -R format
```

Apply `clang-format` to tracked C/C++ files:

```bash
tools/format.sh
```

Configure one case plus its evaluator:

```bash
cmake -S . -B build \
  -DNITR_BUILD_ALL_CASES=OFF \
  -DNITR_CASE=003.reuse-existing-code \
  -DNITR_BUILD_EVALUATOR=ON
```

Configure one case only:

```bash
cmake -S . -B build -DNITR_BUILD_ALL_CASES=OFF -DNITR_CASE=001.add-no-callsite-spread
```

Some starter cases are intentionally incomplete and may not compile before the task is solved. The public corpus is meant to expose the starter state, not a fully solved build.

For local development, manual debugging, or quick validation of one case, you can
configure and build a single case with:

```bash
python3 tools/run_case.py 002.refactor-and-reuse
```

To build a single case and run its public evaluator checks locally:

```bash
python3 tools/run_case.py 002.refactor-and-reuse --with-evaluator
```

Use `tools/run_case.py` when you want to work on one case directly inside the
repository. Use the tooling under [`submit/`](submit/README.md) when you want to
materialize generated submission outputs under `.submit-output/` and evaluate
those results separately.

The evaluator also supports a pipeline-based entrypoint:

```bash
python3 evaluator/run_evaluation_pipeline.py evaluator/002.refactor-and-reuse/pipeline.json
```

This is the current evaluator path for submission-style runs. Each case
`pipeline.json` declares the ordered evaluation modules to run, such as
`build`, `unit_test`, `source_analysis`, `baseline_diff`, `required_paths`, and
`customized_check`.

Python cases still register their functional tests through `CMake` / `CTest`
so they can participate in the same evaluator flow as C++ cases.

The underlying evaluator CMake targets are still registered through
`evaluator/CMakeLists.txt` when `-DNITR_BUILD_EVALUATOR=ON` is enabled. That
file remains the build-target registration layer, while
`evaluator/run_evaluation_pipeline.py` is the primary orchestration entrypoint.

For local regression coverage against already-materialized submit outputs, see
[`evaluator/shared/module/testdata/submission_pipeline/README.md`](evaluator/shared/module/testdata/submission_pipeline/README.md).

When evaluating materialized outputs under `.submit-output/`, you can override
paths from the pipeline config at runtime instead of editing the JSON:

```bash
python3 evaluator/run_evaluation_pipeline.py \
  evaluator/008.map-dip/pipeline.json \
  --override case_root=/abs/path/to/.submit-output/<run>/cases/008.map-dip
```

## Running NITR with Different Interfaces

This public repository does not include a hosted submission service. In the
open release, a "submission" means producing repository edits for a selected
case and then evaluating the result locally with the provided public evaluator
or the helper scripts under `submit/`.

Typical workflow:

```bash
# 1. Pick a case and read its task file(s).
# 2. Ask your coding system to edit files under cases/<case_slug>/.
# 3. Run the public evaluator locally.
python3 tools/run_case.py 002.refactor-and-reuse
python3 tools/run_case.py 002.refactor-and-reuse --with-evaluator
```

You can use the benchmark through several interfaces:

- API workflow: send the selected case directory and its `TASK.md` or
  `TASK1.md`/`TASK2.md`/`TASK3.md` files to your coding agent through an API,
  apply the returned file edits inside this repository, and then run
  `python3 tools/run_case.py <case_slug> --with-evaluator` or
  `python3 evaluator/run_evaluation_pipeline.py evaluator/<case_slug>/pipeline.json`.
- Agent CLI workflow: open this repository in an agentic coding tool, point the
  agent at a specific case, ask it to complete the requested edits in place,
  and then run the same local evaluator command.
- Web chat workflow: if you use a browser-based coding assistant, provide the
  relevant case files and task statement, copy the generated edits back into the
  repository, and then run the local evaluator command here.

For the submit workflow used by this repository and by the paper-aligned
reproduction setup, the agent-visible context is intentionally limited:

- the agent is given the case directory under `cases/<case-slug>/`
- `docs/<case-slug>/SPEC.md` is not part of the agent-visible input
- for multi-step cases, each step receives only the current `TASK*.md`
- later steps continue from the previous step's code state, but do not receive
  earlier `TASK*.md` files again

For multi-step cases, apply the task files in order under that protocol. That
is, complete `TASK1.md` first, continue from the resulting code state to
`TASK2.md`, and so on before running the evaluator.

This repository does not attempt to document every possible external experiment
setup. The notes above describe the submit protocol used here for local
submission tooling and paper-aligned reproduction.

## Cases

- `001.add-no-callsite-spread`
- `002.refactor-and-reuse`
- `003.reuse-existing-code`
- `004.cv-srp`
- `005.pricing-ocp`
- `006.gs-isp`
- `007.ml-lsp-multistep`
- `008.map-dip`
- `009.session-expiry-testability`
- `010.logging-side-effects`
- `011.config-sprawl`
- `012.cache-lifecycle`
- `013.stable-public-api`
- `014.report-export-ocp`
- `015.pipeline-provider-decoupling`
- `016.device-segment-planner`
- `017.active-snapshot-lifecycle`
- `018.seeded-selection-testability`
- `019.ranking-explainability-boundary`
- `020.handover-packet-ownership-boundary`
- `021.inline-filter-entrypoint-reuse`
- `022.thermostat-sensor-decoupling`
- `023.validator-global-mutation`
- `024.metric-recorder-buffered-flush`

## Citation

If you use NITR in your research, please cite the following paper:

```bibtex
@misc{zhu2026nitr,
  title         = {Needle in the Repo: A Benchmark for Maintainability in AI-Generated Repository Edits},
  author        = {Haichao Zhu and Qian Zhang and Jiyuan Wang and Zhaorui Yang and Yuxin Qiu},
  year          = {2026},
  eprint        = {2603.27745},
  archivePrefix = {arXiv},
  primaryClass  = {cs.SE},
  url           = {https://arxiv.org/abs/2603.27745}
}
```

For GitHub citation metadata, see [CITATION.cff](CITATION.cff).

## Contributing

If you want to contribute cases, evaluator updates, or tooling changes, see [CONTRIBUTING.md](CONTRIBUTING.md).
