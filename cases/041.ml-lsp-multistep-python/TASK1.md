## Task

Add `ClampTransform` to the feature-transform subsystem and make the transform
family safe on edge cases.

### Requirements

- `FeatureTransform` remains the shared abstraction.
- `ClampTransform` clamps each value to `[-1.0, 1.0]`.
- Output length must equal input length.
- Input values must not be modified.
- Empty input must return empty output.
- Valid inputs must not throw.
- Outputs must not contain `NaN` or `Inf`.
- `L2NormalizeTransform` must return a unit-norm vector for non-zero input and
  an all-zero vector for all-zero input.

### Constraints

- Do not modify `src/feature_transform.py`.
- Do not modify `src/feature_pipeline.py`.
- You may add new files, modify existing transform implementations, and update
  factory logic.
- Do not modify evaluator files.
- Do not change the abstract interface signature.
