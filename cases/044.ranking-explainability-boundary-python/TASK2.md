## Task

Add a targeted inspection capability for a single candidate in the same ranking engine.

### Requirements
- Keep the ranked-result reason summary working.
- Add an inspection capability that takes the same candidate set plus a candidate id and returns enough information to tell whether that candidate was:
  - excluded before ranking
  - included but ranked lower because of score adjustments
  - ordered behind another candidate because of the tie-break rules
- If a candidate id is unknown, return a clear not-found result.
- The inspection output should be structured data, not free-form paragraphs.

### Constraints
- Do not remove existing ranking behavior.
- Do not turn this into a logging or tracing feature.
- You may add new files under `src/` and update `app/main.py` if needed.
- Keep the implementation deterministic.
- Keep the codebase small and do not add external dependencies.
