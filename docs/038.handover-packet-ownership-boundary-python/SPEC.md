---
case_id: 038-handover-packet-ownership-boundary-python
title: Handover Packet Ownership Boundary, Python
primary_dimension: responsibility_decomposition
secondary_dimensions:
  - side_effect_isolation
  - state_ownership_and_lifecycle
language: Python
granularity: micro
paired_with: 020.handover-packet-ownership-boundary
difficulty: medium
loc: ~140-230
---

# Case 038: Handover Packet Ownership Boundary, Python

## Problem context

A warehouse shift tracker records completed totes and one optional in-progress
tote. Supervisors need to preview the same handover packet that will later be
saved, without changing tracker state or producing inconsistent rows.

## Case metadata and matrix rationale

- Case id / slug: `038-handover-packet-ownership-boundary-python`
- Title: `Handover Packet Ownership Boundary, Python`
- Primary dimension: `D3 Responsibility Decomposition`
- Secondary dimensions: D9 Side-Effect Isolation; D8 State Ownership and Lifecycle
- Granularity: `micro`
- Paired with: `020.handover-packet-ownership-boundary`
- Difficulty: `medium`

Rationale for inclusion:

- This case is a Python paired port of case `020`.
- It preserves the domain-result assembly versus consumer ownership probe.
- Python AST data-flow signals replace C++ include and symbol-pattern checks.

## Given code

Expected starter shape:

```text
- cases/038.handover-packet-ownership-boundary-python/app/main.py
- cases/038.handover-packet-ownership-boundary-python/src/shift_tracker.py
- cases/038.handover-packet-ownership-boundary-python/src/handover_packet.py
- cases/038.handover-packet-ownership-boundary-python/src/handover_packet_preview.py
- cases/038.handover-packet-ownership-boundary-python/src/handover_packet_writer.py
- cases/038.handover-packet-ownership-boundary-python/TASK.md
- evaluator/038.handover-packet-ownership-boundary-python/pipeline.json
- evaluator/038.handover-packet-ownership-boundary-python/tests/test_handover_packet.py
- evaluator/038.handover-packet-ownership-boundary-python/checks/run_evaluator.py
- evaluator/038.handover-packet-ownership-boundary-python/data/
- docs/038.handover-packet-ownership-boundary-python/SPEC.md
```

The starter writer assembles packet rows and summary directly from tracker
state. The preview is a placeholder. Packet data types and a packet renderer
already exist.

## Agent-facing contract

The following section is the full text of `TASK.md`. The internal sections that
follow are not exposed to the coding agent.

## Task

The warehouse handover tool can currently save a handover packet at the end of
a shift, but the save path builds the packet directly from the live tracker
state. We now need a terminal preview so supervisors can inspect the packet
before saving it.

Update the handover flow so preview and save use the same packet content. If
the shift still has one in-progress tote, that tote must appear in the packet.
Packet row numbers and the packet summary must also match between preview and
save. Previewing the packet must not change what later gets saved, and repeated
preview/save calls should stay stable.

### Requirements

- Add support for previewing the handover packet before saving it.
- Keep preview and save consistent for the same tracker state.
- Include the current in-progress tote in the packet when present.
- Preserve correct packet row numbers and packet summary in both preview and
  save.
- Previewing must not change what a later save produces.
- Keep existing behavior unchanged unless required above.

### Constraints

- Do not modify evaluator files.
- Do not add external dependencies.
- Keep the change small and local to this case.

## Expected design direction (human-facing)

Tracker state should be materialized into a complete `HandoverPacket` at a
domain-side boundary. That producer owns inclusion of the in-progress tote,
row numbering, and summary calculation.

Preview and save should obtain and consume the assembled packet. Rendering and
file writing may remain consumer responsibilities, but they should not rebuild
packet content from live tracker fields.

## Hidden evaluator intent

This is a D3 micro case. The key question is whether consumer-side preview and
writer code turns tracker state into packet data, even if that assembly is
deduplicated into a shared output helper.

Behavioral checks alone cannot distinguish that ownership error, so the case
also scans consumer functions for tracker-state and packet-assembly signals and
requires a domain-side producer.

## Functional expectations

- preview text and saved text are identical for the same tracker state
- an in-progress tote appears last and is marked correctly
- a closed tote appears as a normal completed row
- row numbers start at one and remain sequential
- summaries contain exact tote and package totals
- preview-before-save, save-before-preview, and repeated calls remain stable
- preview and save do not mutate the in-progress tote

## Evaluator plan

### Functional checks

The evaluator tests:

- preview and save with an in-progress tote
- preview and save after the current tote has been closed
- repeated preview-then-save calls
- save followed by preview
- sequential row numbering and stable summary values

Expected packet text is stored in evaluator fixtures and compared exactly.

### Structural / oracle checks

The AST evaluator:

- classifies preview, writer, render, output, and app files as consumer-side
- flags consumer functions that combine raw tracker-state access with packet
  row, packet object, numbering, or summary assembly
- scans new Python modules under `src/` so moving the same logic into an
  output-side helper does not bypass the check
- requires at least one non-consumer domain-side function that both reads
  tracker state and produces packet data

The oracle permits alternative names and either a tracker method or a separate
domain assembler. Pure renderers may inspect an already-assembled packet.

## Failure modes (non-scoring)

- copying packet assembly into preview
- leaving packet assembly inside the writer
- sharing one preview/writer helper that still accepts live tracker state
- computing row numbers or summaries in rendering or file-writing code
- mutating or closing the current tote during preview
- producing independently assembled preview and saved content that only happen
  to match the sample scenario

## Maintainability mapping

Primary Dimension:

- D3 Responsibility Decomposition

Measured Capability:

- keep domain-result assembly at a domain-side ownership boundary
- keep preview and save limited to consuming stable packet data
- avoid disguising consumer-side ownership as shared-helper reuse

Secondary Dimensions:

- D9 Side-Effect Isolation
- D8 State Ownership and Lifecycle

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new domain-side files or helpers | Yes |
| Modify tracker and packet implementation | Yes |
| Modify evaluator files | No |
| Add external dependencies | No |
| Let preview/save consume packet data | Yes |
| Assemble packet content in consumer-side code | No |
| Mutate tracker state while previewing or saving | No |
