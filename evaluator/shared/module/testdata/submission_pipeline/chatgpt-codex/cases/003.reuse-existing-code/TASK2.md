## Task

Handle the zero-norm behavior for `nitr::case003::CosineSimilarity(...)` in `src/cosine_similarity.cc`.

### Requirements
- Keep the size-mismatch behavior working.
- Return `0.0` if either input vector has zero L2 norm.

### Constraints
- Reuse `nitr::case003::L2Norm`.
- Keep the change localized to `src/cosine_similarity.cc`.
- Do not modify other files under `src/`.
- Do not modify evaluator files.
