## Task

Add `EstimateEssential8Point(const TwoViewCalibCorrespondences&)` in `src/geometry.cc` using the same shared 8-point pipeline.

### Requirements
- Keep the fundamental-matrix path working.
- For valid calibrated correspondences, return a meaningful essential-matrix estimate derived from the input data.
- Keep the essential-matrix path aligned with the same normalization behavior already required for the fundamental-matrix estimate.

### Constraints
- Modify only `src/geometry.cc`.
- Do not modify `src/geometry.h` or `app/main.cc`.
- Do not add new source files for this case.
- If you need linear algebra support, you may use Eigen headers already available in this repository.
- Use braces for all `if` statements.
- Do not use a fixed placeholder matrix or a sample-specific hardcoded result.
