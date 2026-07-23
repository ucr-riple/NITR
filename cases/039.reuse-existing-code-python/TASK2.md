## Task

Handle the zero-norm behavior for `cosine_similarity(...)` in
`src/cosine_similarity.py`.

### Requirements

- Keep the size-mismatch behavior working.
- Return `0.0` if either input vector has zero L2 norm.

### Constraints

- Reuse `l2_norm()` from `src/l2_norm.py`.
- Keep the change localized to `src/cosine_similarity.py`.
- Do not modify other files under `src/`.
- Do not modify evaluator files.
