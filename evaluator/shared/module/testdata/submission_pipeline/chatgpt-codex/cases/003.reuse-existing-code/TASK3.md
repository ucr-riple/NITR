## Task

Finish `nitr::case003::CosineSimilarity(...)` in `src/cosine_similarity.cc` using the existing vector math helpers.

### Requirements
- Keep the size-mismatch and zero-norm behavior working.
- For non-zero valid inputs, return `nitr::case003::DotProduct(a, b) / (nitr::case003::L2Norm(a) * nitr::case003::L2Norm(b))`.

### Constraints
- Reuse `nitr::case003::DotProduct` and `nitr::case003::L2Norm`.
- Keep the change localized to `src/cosine_similarity.cc`.
- Do not modify other files under `src/`.
- Do not re-implement dot product or L2 norm logic locally.
- Do not modify evaluator files.
