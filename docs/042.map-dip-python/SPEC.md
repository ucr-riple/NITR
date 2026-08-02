---
case_id: 042-map-dip-python
title: Map Provider Dependency Inversion, Python
primary_dimension: dependency_control
secondary_dimensions: []
language: Python
granularity: micro
paired_with: 008.map-dip
difficulty: easy
loc: ~100-160
---

# Case 042: Map Provider Dependency Inversion, Python

## Problem context

A map snapshot service assembles configured layers from an input payload.
Built-in providers work, but the service constructs them directly and rejects
types supplied by independent modules. New layers must become registerable
without adding provider knowledge to snapshot policy.

## Case metadata and matrix rationale

- Case id / slug: `042-map-dip-python`
- Title: `Map Provider Dependency Inversion, Python`
- Primary dimension: `D6 Dependency Control`
- Secondary dimensions: none
- Granularity: `micro`
- Paired with: `008.map-dip`
- Difficulty: `easy`

Rationale for inclusion:

- This is the Python paired port of case `008.map-dip`.
- The starter exposes a registry seam but deliberately bypasses it in the core,
  distinguishing real dependency inversion from decorative abstraction.
- Evaluator-owned providers prove extension from outside the case's concrete
  provider family.

## Given code

```text
- cases/042.map-dip-python/app/main.py
- cases/042.map-dip-python/src/map_snapshot.py
- cases/042.map-dip-python/src/providers_builtin.py
- cases/042.map-dip-python/TASK.md
- evaluator/042.map-dip-python/tests/test_map_snapshot.py
- evaluator/042.map-dip-python/checks/run_evaluator.py
- evaluator/042.map-dip-python/pipeline.json
- docs/042.map-dip-python/SPEC.md
```

The CLI and built-in provider behavior are complete. `LayerProvider`,
`LayerRegistry`, and built-in registration are available, but
`MapSnapshotService` still performs concrete construction and type dispatch.

## Agent-facing contract

The following section reproduces the full text of `TASK.md`. Internal sections
after it are not exposed to the coding agent.

## Task Description

Refactor the implementation to satisfy DIP **without changing the observable
behavior** for existing layers.

### Behavioral requirements

- `map_snapshot` reads a JSON config from a file path argument.
- It reads all stdin as the input payload string.
- It outputs the exact stable text snapshot format expected by the tests,
  including the header line.

### Constraints

You **must not** modify:

- `app/main.py`
- The public signature of `MapSnapshotService.build_snapshot(...)`

You **may**:

- Add new files/classes
- Modify files under `src/`
- Introduce a registry/factory mechanism

### Plugin requirement (killer DIP test)

The evaluator will define and register a new layer type:

- `reverse_payload` — reverses the stdin payload string and returns it as a
  layer.

Your solution must pass this test **without modifying** the snapshot core
logic. Built-in layer support must also avoid hardcoded concrete provider
construction inside the snapshot core.

## Expected design direction (human-facing)

Built-in providers should register creators with `LayerRegistry`. Snapshot
policy should validate the layer list, ask the registry for each provider, and
format results through `LayerProvider`. Provider-specific configuration belongs
in creator functions rather than the service.

## Hidden evaluator intent

This D6 case tests whether the high-level snapshot service genuinely depends on
the provider abstraction. A registry that exists but is bypassed does not pass.

Two evaluator-owned providers are registered at runtime. One reverses payload;
the other consumes provider-specific configuration, proving that the registry
forwards the complete layer object to external creators.

## Functional expectations

- built-in geometry and semantics snapshots remain byte-stable
- an evaluator-owned reverse provider works without core edits
- an evaluator-owned configured provider receives its configuration
- invalid and unknown layer definitions fail
- the protected CLI reads the config and all stdin correctly

## Evaluator plan

### Functional checks

Unit tests cover built-ins, two external registrations, config forwarding,
invalid config, unknown types, and the real CLI through a subprocess.

### Structural / oracle checks

The pipeline protects `app/main.py` with a baseline diff. The AST evaluator
inspects `MapSnapshotService.build_snapshot()` and:

- rejects concrete built-in provider references and imports
- rejects built-in and evaluator type identifiers in snapshot policy
- requires provider creation through the registry's `create()` seam
- requires the public `build_snapshot(self, config, payload)` signature to
  remain unchanged

## Failure modes (non-scoring)

- adding another `if layer_type == ...` branch for the evaluator plugin
- hardcoding built-in providers but using the registry only as a fallback
- importing concrete provider classes into the snapshot service
- registering creators without making the service consume the registry
- changing the CLI or public `build_snapshot()` signature

## Maintainability mapping

Primary Dimension:

- D6 Dependency Control

Measured Capability:

- invert concrete provider construction behind a stable abstraction
- accept implementations owned by external modules
- keep high-level snapshot policy independent of provider details

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Modify files under `src/` | Yes |
| Add provider or registry modules | Yes |
| Modify `app/main.py` | No |
| Modify evaluator files | No |
| Change `build_snapshot()` signature | No |
| Register external provider creators | Yes |
| Hardcode provider dispatch in snapshot policy | No |
