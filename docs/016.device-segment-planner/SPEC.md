```yaml
case_id: 016-device-segment-planner
title: GPU/CPU pipeline segmentation planner
primary_dimension: testability
secondary_dimensions:
  - responsibility_separation
  - change_locality
language: C++
difficulty: medium
loc: ~220
```

## Problem Context

This pipeline tool executes a sequence of ML processing steps from a config file.
Some steps require GPU placement while others are CPU-only.
Running everything on a GPU machine wastes GPU time once later work becomes CPU-bound.
The system now needs config-driven segmentation that coalesces consecutive same-device steps.

## Given Code

The starter code compiles and the smoke tests pass.
It can parse a small JSON config shape and execute all listed steps.
The current implementation is intentionally GPU-centric: `BuildExecutionPlan(...)` always returns one GPU segment, and `PipelineRunner::Run(...)` still executes every step on GPU.
This leaves the starter code with the intended pressure point: segmentation behavior is not yet correct and the runner does not yet consume a correct config-driven plan.

## TASK.md Section (Agent-Facing)

## Task

Update the pipeline execution tool so device placement comes from the config instead of assuming the whole pipeline runs on GPU.
The system must support both the older config style and the newer per-step device style, while keeping execution behavior deterministic.

### Requirements
- Support the legacy case where `legacy_gpu_through_step: 4` means steps 1-4 run on GPU and steps 5-8 run on CPU.
- Support the updated case where step-level device requirements produce `GPU: 1-4`, `CPU: 5`, `GPU: 6`, `CPU: 7-8`.
- Generalize to arbitrary valid configs by coalescing consecutive same-device-required steps into one segment.
- Keep backward compatibility for the existing config loader and command-line entrypoint.

### Constraints
- Do not modify files under `evaluator/016.device-segment-planner/`.
- You may add new files under `src/`.
- Do not add third-party dependencies.
- Keep existing behavior unchanged unless required above.

## Expected Design Direction

Acceptable solutions make segmentation directly observable from config-driven input and keep execution consistent with the computed segmentation result.
The exact class or function names do not matter, but the resulting code should support direct assertions on device segments without relying on log parsing.
Undesirable patterns include scenario-specific branching on known indices, duplicating old and new config behavior in separate code paths, or burying placement rules in device-specific execution code.

## Evaluation Criteria

### Functional
- All existing smoke tests must still pass.
- Legacy config produces two segments: GPU 0-3 and CPU 4-7.
- Updated config produces four segments: GPU 0-3, CPU 4-4, GPU 5-5, CPU 6-7.
- Unseen configs are segmented correctly by coalescing consecutive same-device steps.
- Runner output uses the correct device assignment for each executed step.

### Structural
- Evaluator includes at least one test that calls the planning entrypoint directly and asserts returned segment boundaries and devices from input config data.
- Runner path must consume computed segmentation behavior rather than silently re-encoding all placement rules in a separate path.
- Hardcoded branching on known step indices in core source files is forbidden.
- Modifying files under `evaluator/016.device-segment-planner/` is forbidden.

### Maintainability
- Segmentation behavior is directly assertable without running real infrastructure.
- Planning remains deterministic across legacy, updated, and unseen configs.
- Responsibility separation supports plan-level testing without making D3 the primary scoring axis.
- Auxiliary static checks support, but do not replace, direct plan-level assertions.

## Oracle Signals

- `execution_plan_legacy_test`
- `execution_plan_updated_test`
- `execution_plan_unseen_test`
- `runner_respects_segmentation_test`
- pipeline structural checks that:
  - require `pipeline_runner.cc` to call `BuildExecutionPlan(...)`
  - forbid hardcoded legacy step-index special-casing in production source
  - remain auxiliary only

Static checks are supportive only.
They cannot pass a submission without direct plan-level assertions and unseen-config functional coverage.

## Failure Modes (Non-scoring)

- Patches known step numbers directly inside runner logic.
- Implements separate legacy and updated code paths with duplicated placement rules.
- Leaves the runner independent from the computed segmentation result.
- Relies on log inspection instead of directly assertable plan data.
- Passes known examples but fails unseen segmentation patterns.

## Maintainability Mapping

Primary Dimension:
  - testability
Measured Capability:
  - deterministic plan-level assertions
  - low-friction validation of segmentation behavior
Secondary Dimensions:
  - responsibility_separation
  - change_locality

## Allowed & Disallowed Summary

| Action                         | Allowed |
|--------------------------------|---------|
| Add new files                  | Yes     |
| Modify existing core logic     | Yes     |
| Modify existing tests          | No      |
| Add new dependencies           | No      |
| Modify public headers          | Yes     |
| Use global mutable state       | No      |
| Introduce new external IO      | No      |
