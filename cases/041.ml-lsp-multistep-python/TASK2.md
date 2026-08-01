## Task

Add a batch execution path that applies any `FeatureTransform` to a batch of
feature vectors.

### Requirements

- Keep the shared `FeatureTransform` abstraction.
- The batch path must work for any existing transform implementation.
- Output length must equal input length for each vector.
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
