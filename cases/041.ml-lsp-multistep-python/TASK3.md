## Task

Add transform chaining so multiple transforms can be applied sequentially
through the same abstraction.

### Requirements

- Keep the shared `FeatureTransform` abstraction.
- Chaining must work with the existing transforms and any new transform added
  for this case.
- Output length must equal input length.
- Input values must not be modified.
- Empty input must return empty output.
- Valid inputs must not throw.
- Outputs must not contain `NaN` or `Inf`.

### Constraints

- Do not modify `src/feature_transform.py`.
- Do not modify `src/feature_pipeline.py`.
- You may add new files, modify existing transform implementations, and update
  factory logic.
- Do not modify evaluator files.
- Do not change the abstract interface signature.
- Do not bypass the abstraction by specializing callers on concrete transform
  types.
