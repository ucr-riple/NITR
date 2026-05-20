## Task

Refine `src/geometry.cc` so both two-view estimation entry points remain working after the second feature is added, while keeping the implementation small and maintainable.

### Requirements
- Keep both `EstimateFundamental8Point(...)` and `EstimateEssential8Point(...)` working.
- Keep both estimates driven by the provided correspondence data rather than fixed or sample-specific outputs.

### Constraints
- Modify only `src/geometry.cc`.
- Do not modify `src/geometry.h` or `app/main.cc`.
- Do not add new source files for this case.
- If you need linear algebra support, you may use Eigen headers already available in this repository.
- Use braces for all `if` statements.
