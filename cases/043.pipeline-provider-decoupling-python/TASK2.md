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
