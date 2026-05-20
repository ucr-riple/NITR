## Task

Implement `EstimateFundamental8Point(const TwoViewCorrespondences&)` in `src/geometry.cc` while keeping the existing declarations and call sites unchanged.

### Requirements
- For valid two-view correspondences, return a meaningful fundamental-matrix estimate derived from the input data.
- Use a normalized estimation path so the result remains stable on the provided correspondence data.

### Constraints
- Modify only `src/geometry.cc`.
- Do not modify `src/geometry.h` or `app/main.cc`.
- Do not add new source files for this case.
- If you need linear algebra support, you may use Eigen headers already available in this repository.
- Use braces for all `if` statements.
- Do not use a fixed placeholder matrix or a sample-specific hardcoded result.
