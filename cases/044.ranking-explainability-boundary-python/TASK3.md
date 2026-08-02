## Task

Finish the explainability feature by adding a comparison capability for two ranked candidates.

### Requirements
- Keep the ranked-result reason summary and single-candidate inspection capability working.
- Add a comparison capability for two candidates that are both present in the ranked result.
- The comparison output should explain why one ranked above the other using the existing score and tie-break rules.
- If the comparison request references a candidate that is not in the ranked result, return a clear unsupported or not-applicable result.
- The output should be structured data, not free-form paragraphs.

### Constraints
- Do not remove existing ranking behavior.
- Do not turn this into a logging or tracing feature.
- You may add new files under `src/` and update `app/main.py` if needed.
- Keep the implementation deterministic.
- Keep the codebase small and do not add external dependencies.
