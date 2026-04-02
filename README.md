# Needle in the Repo: A Benchmark for Maintainability in AI-Generated Repository Edits
Haichao Zhu*, Qian Zhang*, Jiyuan Wang, Zhaorui Yang, and Yuxin Qiu (* indicates equal contribution)
<br>
| [arXiv](https://arxiv.org/abs/2603.27745) | [Project Page](https://www.cs.ucr.edu/~qzhang/nitr.html) |

TL;DR: Needle in the Repo (NITR) is a C++ repository-level benchmark for evaluating whether
AI-generated repository edits preserve maintainable structure, not just
behavioral correctness. It comprises 21 curated C++ repository probes across
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

## Overview

This repository contains the public benchmark release:

- 21 starter cases under `cases/`
- case specifications and design docs under `docs/`
- public evaluator code under `evaluator/`
- agent-facing task statements (`TASK.md`, `TASK1.md`, ...)
- vendored dependencies required to build cases and evaluators

This repository excludes submission tooling.

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

## Build

Configure all cases:

```bash
cmake -S . -B build
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

For a lightweight public runner, you can configure and build a single case with:

```bash
python3 tools/run_case.py 002.refactor-and-resue
```

To build a single case and run its public evaluator checks:

```bash
python3 tools/run_case.py 002.refactor-and-resue --with-evaluator
```

## Running NITR with Different Interfaces

This public repository does not include a hosted submission service. In the
open release, a "submission" means producing repository edits for a selected
case and then evaluating the result locally with the provided public evaluator.

Typical workflow:

```bash
# 1. Pick a case and read its task file(s).
# 2. Ask your coding system to edit files under cases/<case_slug>/.
# 3. Run the public evaluator locally.
python3 tools/run_case.py 002.refactor-and-resue
python3 tools/run_case.py 002.refactor-and-resue --with-evaluator
```

You can use the benchmark through several interfaces:

- API workflow: send the selected case directory and its `TASK.md` or
  `TASK1.md`/`TASK2.md`/`TASK3.md` files to your coding agent through an API,
  apply the returned file edits inside this repository, and then run
  `python3 tools/run_case.py <case_slug> --with-evaluator`.
- Agent CLI workflow: open this repository in an agentic coding tool, point the
  agent at a specific case, ask it to complete the requested edits in place,
  and then run the same local evaluator command.
- Web chat workflow: if you use a browser-based coding assistant, provide the
  relevant case files and task statement, copy the generated edits back into the
  repository, and then run the local evaluator command here.

For multi-step cases, apply the task files in order. That is, complete
`TASK1.md` first, continue from the resulting code state to `TASK2.md`, and so
on before running the evaluator.

## Cases

- `001.add-no-callsite-spread`
- `002.refactor-and-resue`
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

## Citation

```bibtex
@misc{zhu2026nitr,
  title        = {Needle in the Repo: A Benchmark for Maintainability in AI-Generated Repository Edits},
  author       = {Haichao Zhu and Qian Zhang and Jiyuan Wang and Zhaorui Yang and Yuxin Qiu},
  year         = {2026},
  eprint       = {arXiv:2603.27745},
  archivePrefix = {arXiv},
  primaryClass = {cs.SE},
  url          = {https://arxiv.org/abs/2603.27745}
}
```
