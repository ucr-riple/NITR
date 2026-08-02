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
