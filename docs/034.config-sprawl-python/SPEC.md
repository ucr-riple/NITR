---
case_id: 034-config-sprawl-python
title: Config Sprawl, Python
primary_dimension: change_locality
secondary_dimensions: []
language: Python
granularity: micro
paired_with: 011.config-sprawl
difficulty: easy
loc: ~70-130
---

# Case 034: Config Sprawl, Python

## Problem context

An inventory report renderer already supports an `include_summary` option.
It now needs a compact mode that changes the header, rows, and summary format
while leaving the existing full report unchanged.

## Case metadata and matrix rationale

- Case id / slug: `034-config-sprawl-python`
- Title: `Config Sprawl, Python`
- Primary dimension: `D1 Change Locality`
- Secondary dimensions: none
- Granularity: `micro`
- Paired with: `011.config-sprawl`
- Difficulty: `easy`

Rationale for inclusion:

- This case is a Python paired port of case `011.config-sprawl`.
- It preserves the same configuration-boundary and signature-sprawl probe.
- Python AST analysis replaces the C++ signature-pattern oracle.

## Given code

Expected starter shape:

```text
- cases/034.config-sprawl-python/app/main.py
- cases/034.config-sprawl-python/src/report_types.py
- cases/034.config-sprawl-python/src/report_renderer.py
- cases/034.config-sprawl-python/TASK.md
- cases/034.config-sprawl-python/CMakeLists.txt
- evaluator/034.config-sprawl-python/pipeline.json
- evaluator/034.config-sprawl-python/tests/test_config_sprawl.py
- evaluator/034.config-sprawl-python/checks/run_evaluator.py
- evaluator/034.config-sprawl-python/data/expected_outputs.txt
- docs/034.config-sprawl-python/SPEC.md
```

The starter renders the existing full report. `ReportOptions` contains the
existing `include_summary` setting, and the compact mode is not implemented.

## Agent-facing contract

The following section is the full text of `TASK.md`. The internal sections that
follow are not exposed to the coding agent.

# Task

Implement support for a compact rendering mode in the inventory report.

## Requirements

Add a new field to `ReportOptions`:

- `compact_mode` with default value `False`

Keep the existing full mode behavior unchanged.

When `compact_mode` is `True`:

- the header must be exactly:
  `Inventory Report (compact)`
- each row must be rendered as:
  `<id>:<name>:<quantity>`
- if `include_summary` is `True`, the summary must be exactly:
  `Total quantity: <sum>`
- if `include_summary` is `False`, omit the summary

## Expected design direction (human-facing)

`ReportOptions` should remain the object that carries renderer configuration.
Helpers may consume the options object or use another localized internal
design, but they should not receive a separately threaded `compact_mode` flag.
The public renderer entrypoint should remain unchanged.

## Hidden evaluator intent

This is a D1 micro case. The maintainability signal is whether one configuration
change stays behind the existing options boundary or amplifies into standalone
parameters across renderer signatures.

The evaluator does not require one exact helper decomposition. It rejects the
specific change-amplification pattern in which `compact_mode` becomes another
parameter that callers must repeatedly forward.

## Functional expectations

- full mode output remains byte-for-byte unchanged
- compact mode uses its exact header and row formats
- compact summary contains only the total-quantity line
- summary omission works in compact mode
- `compact_mode` defaults to `False`
- arbitrary item lists render correctly

## Evaluator plan

### Functional checks

The evaluator tests:

- existing full output with summary
- compact output with summary
- compact output without summary
- the `compact_mode=False` default
- compact rendering and totals for a non-sample item list

The starter should fail compact-mode tests until the task is implemented while
continuing to pass the existing full-mode behavior.

### Structural / oracle checks

The evaluator parses Python files under `src/` with Python's AST and inspects
every function and method signature. Any standalone parameter named
`compact_mode` fails the structural check. Configuration should instead flow
through `ReportOptions` or remain localized inside the renderer.

The structural check is intentionally narrow and mirrors the paired C++ case's
signature-level oracle without enforcing exact helper names or decomposition.

## Failure modes (non-scoring)

- adding `compact_mode` to the public renderer function signature
- adding `compact_mode` to header, row, or footer helper signatures
- manually forwarding the same standalone flag through multiple call layers
- changing the established full-mode output while adding compact mode
- adding unrelated configuration plumbing or public API surface

## Maintainability mapping

Primary Dimension:

- D1 Change Locality

Measured Capability:

- extend an existing configuration object without spreading standalone flags
- keep a small behavior change localized behind the existing options boundary

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new files under `src/` | Yes |
| Modify existing source files | Yes |
| Modify evaluator files | No |
| Add external dependencies | No |
| Extend `ReportOptions` | Yes |
| Add standalone `compact_mode` function parameters | No |
| Change existing full-mode output | No |
