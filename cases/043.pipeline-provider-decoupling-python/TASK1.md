## Task

Add policy enrichment to the existing event pipeline outputs using the built-in static policy source.

### Requirements
- Add `policy_tier` and `retention_days` to enriched output records.
- Policy lookup must support the `static` policy source.
- Keep baseline (non-policy) pipeline behavior unchanged except for the new enrichment fields.

### Constraints
- Do not add external libraries beyond what is already used in this repository.
- Keep changes small and focused; avoid unrelated refactors.
