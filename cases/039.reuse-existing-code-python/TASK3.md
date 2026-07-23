## Task

Finish `cosine_similarity(...)` in `src/cosine_similarity.py` using the
existing vector math helpers.

### Requirements

- Keep the size-mismatch and zero-norm behavior working.
- For non-zero valid inputs, return
  `dot_product(a, b) / (l2_norm(a) * l2_norm(b))`.

### Constraints

- Reuse `dot_product()` from `src/dot_product.py` and `l2_norm()` from
  `src/l2_norm.py`.
- Keep the change localized to `src/cosine_similarity.py`.
- Do not modify other files under `src/`.
- Do not re-implement dot product or L2 norm logic locally.
- Do not modify evaluator files.
