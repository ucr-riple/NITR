---
case_id: 025-extend-benchmark-modelvmodel
title: Detector Benchmark Metric Boundary
primary_dimension: responsibility_decomposition
secondary_dimensions:
  - side_effect_isolation
language: C++
difficulty: easy-medium
loc: ~160
---

## Problem Context

A detector benchmark compares AI model families such as D-FINE and RT-DETR using
published benchmark rows. The current benchmark can identify the highest-AP
model, but product users also want a speed-adjusted winner that balances
accuracy with throughput.

The design pressure is maintainability:
- keep benchmark orchestration separate from metric formulas
- keep raw model benchmark facts separate from derived scores
- preserve a small path for adding future metrics

## Given Code

Starter code provides:
- `src/benchmark_record.h` with raw benchmark row data
- `src/benchmark_data.*` with D-FINE and RT-DETR fixture rows
- `src/scoreboard.*` with existing accuracy ranking behavior
- `src/benchmark_runner.*` with the benchmark summary entrypoint
- `app/main.cc` entrypoint
- evaluator tests and a metric-boundary structural check

Initial state compiles, but the new speed-adjusted behavior is not implemented.

## Agent-Facing Contract

This text must match `cases/025.extend_benchmark_modelvmodel/TASK.md`.

## Task

Extend the detector benchmark so it reports both the highest-accuracy model and
the best speed-adjusted model.

### Requirements
- Keep the existing accuracy-based benchmark behavior working.
- Add a speed-adjusted score computed as `average_precision * fps / 100.0`.
- Report both the accuracy winner and the speed-adjusted winner in the final
  benchmark summary.
- Preserve support for comparing D-FINE and RT-DETR benchmark rows.

### Constraints
- Do not modify `app/main.cc`.
- You may modify files under `src/` and add new files under `src/` if needed.
- Do not modify evaluator files.

## Expected Design Direction

Derived scoring should live outside the benchmark runner. The benchmark runner
should coordinate records, rankings, and summary assembly. Raw benchmark rows
should continue to represent source facts such as AP and FPS, not store derived
scores as input data.

Recommended shape:
- add a scoring, ranking, or comparison helper under `src/`
- keep `BenchmarkRecord` as raw benchmark data
- keep `RunBenchmark` as orchestration
- let summary formatting consume already-computed winners

## Hidden Evaluator Intent

Primary maintainability probe:
- D3 Responsibility Decomposition

The evaluator rewards:
- correct AP winner behavior
- correct speed-adjusted winner behavior
- derived score computation outside `benchmark_runner.cc`
- no hard-coded model-family bonuses or special cases

The evaluator penalizes:
- inspecting raw benchmark fields or computing score formulas directly in
  `benchmark_runner.cc`
- storing derived speed-adjusted scores in the source benchmark fixture rows
- replacing AP ranking with only the new metric
- hard-coding D-FINE or RT-DETR names into score logic

## Evaluation Criteria

### Functional
- accuracy winner is still selected by AP
- speed-adjusted winner is selected by `average_precision * fps / 100.0`
- default D-FINE and RT-DETR rows are supported
- summary formatting includes both winners

### Structural
- derived scoring is separated from benchmark orchestration
- benchmark orchestration stays in the runner
- benchmark rows remain raw model statistics

## Distinctness and Mapping

Primary Dimension:
- D3 Responsibility Decomposition

Measured Capability:
- keep derived score computation separate from procedural benchmark flow

Secondary Dimension:
- D9 Side-Effect Isolation

Why this case is different:
- Existing D3 cases cover computer-vision pipeline boundaries and ownership
  boundaries. This case focuses on benchmark procedure versus score computation:
  the runner should coordinate records and summaries while scoring logic remains
  in a separate helper or component.
