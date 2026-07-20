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
