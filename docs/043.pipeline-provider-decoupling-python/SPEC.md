---
case_id: 043-pipeline-provider-decoupling-python
title: Pipeline Provider Decoupling, Python
primary_dimension: dependency_control
secondary_dimensions: []
language: Python
granularity: multi-step
paired_with: 015.pipeline-provider-decoupling
difficulty: medium
loc: ~150-230
---

# Case 043: Pipeline Provider Decoupling, Python

## Problem context

An event pipeline emits normalized records and must optionally enrich them with
policy metadata. Static and file-backed policy sources are selected by
configuration, while the execution core must remain independent of backend
selection and construction.

## Case metadata and matrix rationale

- Case id / slug: `043-pipeline-provider-decoupling-python`
- Primary dimension: `D6 Dependency Control`
- Granularity: `multi-step`
- Paired with: `015.pipeline-provider-decoupling`
- Difficulty: `medium`

This Python port preserves the three-stage provider pressure. Unlike the
registry-oriented Case 042, it measures a single composition boundary and an
injected provider contract consumed by `PipelineRunner`.

## Given code

The starter contains event, policy, configuration, abstract provider, static
provider, file provider, runner, and `build_pipeline()` composition modules.
Provider implementations are complete; enrichment and composition wiring are
placeholders.

## Agent-facing contract

The following sections reproduce the full task texts.

## Task 1

## Task

Add policy enrichment to the existing event pipeline outputs using the built-in static policy source.

### Requirements
- Add `policy_tier` and `retention_days` to enriched output records.
- Policy lookup must support the `static` policy source.
- Keep baseline (non-policy) pipeline behavior unchanged except for the new enrichment fields.

### Constraints
- Do not add external libraries beyond what is already used in this repository.
- Keep changes small and focused; avoid unrelated refactors.

## Task 2

## Task

Extend policy enrichment so the pipeline can also load policy data from the `file` policy source.

### Requirements
- Keep the `static` policy source working.
- Add support for the `file` policy source selected by configuration.
- Add `policy_tier` and `retention_days` to enriched output records for both policy sources.
- For unknown sources, apply fallback policy:
  - `policy_tier=standard`
  - `retention_days=30`

### Constraints
- Do not add external libraries beyond what is already used in this repository.
- Keep changes small and focused; avoid unrelated refactors.

## Task 3

## Task

Finish the policy enrichment feature so source selection is configuration-driven without changing the baseline pipeline behavior.

### Requirements
- Keep both `static` and `file` policy lookup working.
- Mode selection must be configuration-driven.
- For unknown sources, apply fallback policy:
  - `policy_tier=standard`
  - `retention_days=30`
- Keep existing build and tests passing, and add or update code needed for this feature.

### Constraints
- Do not add external libraries beyond what is already used in this repository.
- Keep changes small and focused; avoid unrelated refactors.

## Expected design direction (human-facing)

`build_pipeline()` should be the composition root that selects and owns a
concrete provider from configuration. `PipelineRunner` should know only
`PolicyProvider`, use it for enrichment, and retain exact baseline output when
enrichment is disabled.

## Hidden evaluator intent

The D6 signal is separation between provider selection and provider use. An
evaluator-owned provider is passed directly to the runner to prove the contract
is real. Static/file outputs deliberately differ so configuration switching
cannot pass accidentally.

## Functional expectations

- disabled enrichment preserves baseline lines exactly
- static and file modes produce their distinct expected policies
- missing source IDs use `standard` and 30 days
- unknown modes enrich with fallback policy
- an evaluator-defined provider substitutes in `PipelineRunner`

## Evaluator plan

### Functional checks

Tests execute baseline, static, file, unknown-mode, fallback, and an
evaluator-owned provider through the public pipeline surfaces.

### Structural / oracle checks

AST analysis rejects concrete providers and mode/path selection in
`pipeline_runner.py`, requires both concrete providers to be wired in
`build_pipeline.py`, and rejects concrete wiring in every other non-provider
source module.

## Failure modes (non-scoring)

- selecting providers or reading mode/path inside `PipelineRunner`
- constructing providers in multiple locations
- bypassing `build_pipeline()` in mode-switching behavior
- branching on concrete providers during enrichment
- changing baseline output while enrichment is disabled

## Maintainability mapping

Primary Dimension:

- D6 Dependency Control

Measured Capability:

- keep execution policy dependent only on a provider contract
- centralize concrete backend choice in one composition boundary
- substitute external providers without core changes

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Modify source files | Yes |
| Wire providers in `build_pipeline.py` | Yes |
| Add external dependencies | No |
| Select providers inside `PipelineRunner` | No |
| Modify evaluator files | No |
