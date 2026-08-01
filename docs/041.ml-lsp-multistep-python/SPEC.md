---
case_id: 041-ml-lsp-multistep-python
title: ML Transform Substitutability, Python
primary_dimension: interface_and_substitutability_discipline
secondary_dimensions: []
language: Python
granularity: multi-step
paired_with: 007.ml-lsp-multistep
difficulty: medium
loc: ~140-220
---

# Case 041: ML Transform Substitutability, Python

## Problem context

A feature-transform subsystem applies vector transformations through one shared
abstraction. It must gain clamping, batch execution, and transform composition
while preserving the same behavioral contract for built-in and future
implementations.

## Case metadata and matrix rationale

- Case id / slug: `041-ml-lsp-multistep-python`
- Title: `ML Transform Substitutability, Python`
- Primary dimension: `D5 Interface and Substitutability Discipline`
- Secondary dimensions: none
- Granularity: `multi-step`
- Paired with: `007.ml-lsp-multistep`
- Difficulty: `medium`

Rationale for inclusion:

- This is the Python paired port of case `007.ml-lsp-multistep`.
- Three related steps exercise the abstraction through a pipeline, a second
  batch caller, and composition.
- An evaluator-owned transform distinguishes genuinely generic callers from
  implementations specialized only for the starter's concrete classes.

## Given code

```text
- cases/041.ml-lsp-multistep-python/app/main.py
- cases/041.ml-lsp-multistep-python/src/feature_transform.py
- cases/041.ml-lsp-multistep-python/src/feature_pipeline.py
- cases/041.ml-lsp-multistep-python/src/identity_transform.py
- cases/041.ml-lsp-multistep-python/src/l2_normalize_transform.py
- cases/041.ml-lsp-multistep-python/src/clamp_transform.py
- cases/041.ml-lsp-multistep-python/src/transform_batch.py
- cases/041.ml-lsp-multistep-python/src/transform_chain.py
- cases/041.ml-lsp-multistep-python/src/transform_factory.py
- cases/041.ml-lsp-multistep-python/TASK1.md
- cases/041.ml-lsp-multistep-python/TASK2.md
- cases/041.ml-lsp-multistep-python/TASK3.md
- evaluator/041.ml-lsp-multistep-python/tests/test_transforms.py
- evaluator/041.ml-lsp-multistep-python/checks/run_evaluator.py
- evaluator/041.ml-lsp-multistep-python/pipeline.json
```

`FeatureTransform` and `FeaturePipeline` are complete and protected. Identity
is complete; L2 normalization is unsafe on zero vectors; clamp, batch, and
chain behavior are placeholders. The factory already exposes all built-ins.

## Agent-facing contract

The following sections reproduce the full texts of `TASK1.md`, `TASK2.md`, and
`TASK3.md`. Internal sections after them are not exposed to the coding agent.

## Task 1

## Task

Add `ClampTransform` to the feature-transform subsystem and make the transform
family safe on edge cases.

### Requirements

- `FeatureTransform` remains the shared abstraction.
- `ClampTransform` clamps each value to `[-1.0, 1.0]`.
- Output length must equal input length.
- Input values must not be modified.
- Empty input must return empty output.
- Valid inputs must not throw.
- Outputs must not contain `NaN` or `Inf`.
- `L2NormalizeTransform` must return a unit-norm vector for non-zero input and
  an all-zero vector for all-zero input.

### Constraints

- Do not modify `src/feature_transform.py`.
- Do not modify `src/feature_pipeline.py`.
- You may add new files, modify existing transform implementations, and update
  factory logic.
- Do not modify evaluator files.
- Do not change the abstract interface signature.

## Task 2

## Task

Add a batch execution path that applies any `FeatureTransform` to a batch of
feature vectors.

### Requirements

- Keep the shared `FeatureTransform` abstraction.
- The batch path must work for any existing transform implementation.
- Output length must equal input length for each vector.
- Input values must not be modified.
- Empty input must return empty output.
- Valid inputs must not throw.
- Outputs must not contain `NaN` or `Inf`.

### Constraints

- Do not modify `src/feature_transform.py`.
- Do not modify `src/feature_pipeline.py`.
- You may add new files, modify existing transform implementations, and update
  factory logic.
- Do not modify evaluator files.
- Do not change the abstract interface signature.
- Do not bypass the abstraction by specializing callers on concrete transform
  types.

## Task 3

## Task

Add transform chaining so multiple transforms can be applied sequentially
through the same abstraction.

### Requirements

- Keep the shared `FeatureTransform` abstraction.
- Chaining must work with the existing transforms and any new transform added
  for this case.
- Output length must equal input length.
- Input values must not be modified.
- Empty input must return empty output.
- Valid inputs must not throw.
- Outputs must not contain `NaN` or `Inf`.

### Constraints

- Do not modify `src/feature_transform.py`.
- Do not modify `src/feature_pipeline.py`.
- You may add new files, modify existing transform implementations, and update
  factory logic.
- Do not modify evaluator files.
- Do not change the abstract interface signature.
- Do not bypass the abstraction by specializing callers on concrete transform
  types.

## Expected design direction (human-facing)

Each concrete transform should own its edge-case behavior. `transform_batch()`
should invoke the shared `transform()` method for every vector. `TransformChain`
should itself implement `FeatureTransform` and pass each intermediate result to
the next abstract step. Neither generic caller should know the concrete
transform family.

## Hidden evaluator intent

This D5 multi-step case measures behavioral substitutability across multiple
callers. Merely inheriting from the ABC is insufficient if batch or chain code
branches on the known subclasses.

The functional evaluator supplies an `OffsetTransform` unknown to the case.
Both generic paths must execute it correctly, proving that the shared contract
rather than a closed concrete-type list controls behavior.

## Functional expectations

- clamp applies the closed `[-1.0, 1.0]` bounds without mutating input
- identity, clamp, and L2 satisfy the shared size, empty, and finiteness contract
- L2 returns zero for zero vectors and unit norm otherwise
- batch works with every built-in and an evaluator-defined transform
- chain applies steps in order and works through `FeaturePipeline`
- an empty chain returns an equal but independent list

## Evaluator plan

### Functional checks

Python tests exercise every transform through the shared pipeline, batch calls
with built-in and evaluator-owned implementations, ordered composition, chain
substitution through the original pipeline, input preservation, and edge cases.

### Structural / oracle checks

The pipeline locks `feature_transform.py` and `feature_pipeline.py` against the
starter baseline. The AST evaluator scans both generic caller modules and:

- rejects imports or references to concrete built-in transform types
- rejects `isinstance()`, `issubclass()`, and `type()` inspection
- requires batch execution to call the shared `transform()` method
- requires `TransformChain` to implement `FeatureTransform`
- requires chain composition to call the shared `transform()` method

## Failure modes (non-scoring)

- repairing zero normalization in a caller instead of the L2 implementation
- branching on concrete transform classes in batch or chain code
- supporting only the three built-ins rather than arbitrary implementations
- making `TransformChain` a special caller that cannot substitute as a transform
- mutating an input vector or returning the same input list from an empty chain
- modifying the protected abstraction or original pipeline

## Maintainability mapping

Primary Dimension:

- D5 Interface and Substitutability Discipline

Measured Capability:

- preserve one contract across implementations and callers
- accept future implementations through the same abstraction
- compose transforms without leaking concrete-type knowledge

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Modify concrete transform implementations | Yes |
| Modify batch and chain modules | Yes |
| Update factory logic | Yes |
| Add transform implementation files | Yes |
| Modify `feature_transform.py` | No |
| Modify `feature_pipeline.py` | No |
| Modify evaluator files | No |
| Branch on concrete types in generic callers | No |
