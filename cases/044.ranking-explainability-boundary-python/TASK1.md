## Task

Extend ranked results so they include a compact structured reason summary for each returned item.

### Requirements
- Keep the existing ranking rules and output order unchanged unless a requirement below adds new returned data.
- For each ranked item, return a compact structured reason summary that includes:
  - the final score
  - the strongest positive factor that helped the item
  - the strongest negative factor, if any
- Keep the implementation deterministic.

### Constraints
- Do not remove existing ranking behavior.
- Do not turn this into a logging or tracing feature.
- You may add new files under `src/` and update `app/main.py` if needed.
- Keep the codebase small and do not add external dependencies.
