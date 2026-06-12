# Case Specification

## 1. Case Metadata

```yaml
case_id:        computer_vision-maintain-8point-shared-normalization
domain:         computer_vision
principle:      N/A  # NITR: duplication control / shared internal step reuse
difficulty:     easy
language:       C++20
loc:            ~250-400
```

---

## 2. Problem Context

Two-view geometry pipelines often implement multiple estimators that share internal numeric steps.
A common example is the normalized 8-point method, where Hartley point normalization is required for stability.
In practice, teams want shared steps implemented once to avoid drift and copy/paste bugs.
This case uses Fundamental (F) and Essential (E) matrix estimation to expose reuse vs duplication.
The JSON I/O glue is handled by the app; the core math lives in `src/`.

---

## 3. Given Code

The repository provides:
- `app/main.cc`: JSON parsing and printing (already complete; do not modify).
- `src/geometry.h`: public data types and function declarations (fixed; do not modify).
- `src/geometry.cc`: stub or incomplete implementations for the required functions.

The code must compile under C++20 with CMake. The evaluator provides datasets and tests.

---

## 4. Task Description

### Public API (Do Not Change)

You must implement the following functions exactly as declared:

```cpp
// src/geometry.h (fixed)
#pragma once
#include <array>
#include <vector>

struct Vec2 { double x = 0.0; double y = 0.0; };
using Mat3 = std::array<double, 9>;   // row-major 3x3

struct TwoViewCorrespondences {
  std::vector<Vec2> pts1;  // pixel coordinates
  std::vector<Vec2> pts2;  // pixel coordinates
};

struct TwoViewCalibCorrespondences {
  std::vector<Vec2> pts1;  // pixel coordinates
  std::vector<Vec2> pts2;  // pixel coordinates
  Mat3 K1;                 // intrinsics
  Mat3 K2;
};

Mat3 EstimateFundamental8Point(const TwoViewCorrespondences& data);       // m1
Mat3 EstimateEssential8Point(const TwoViewCalibCorrespondences& data);    // m2
```

### Milestone 1 (m1)

Implement `EstimateFundamental8Point` using the **normalized 8-point algorithm**:

1. **Hartley normalization** of `pts1` and `pts2` (see §6.1).
2. Build the linear system `A f = 0` from normalized correspondences.
3. Solve for `F_norm` (e.g., SVD least-squares for the smallest singular vector).
4. Enforce `rank(F_norm) = 2` (set smallest singular value to 0).
5. Denormalize: `F = T2^T * F_norm * T1`.
6. Return `F` as row-major `Mat3`.

### Milestone 2 (m2)

Implement `EstimateEssential8Point`:

1. Apply the **same Hartley normalization behavior** to `pts1` and `pts2`.
2. Estimate `F` using the same 8-point procedure as in m1 (internal reuse allowed).
3. Compute `E_raw = K2^T * F * K1`.
4. Enforce essential constraints by SVD:
   - set singular values to `(1, 1, 0)` (or `(s, s, 0)` for `s > 0`), then reconstruct.
5. Return `E` as row-major `Mat3`.

### File restrictions

- You may modify: `src/geometry.cc`
- You must not modify: `src/geometry.h`, `app/main.cc`, anything under `evaluator/002.refactor-and-reuse/`
- Do not add new source files for this case.

---

## 5. Expected Design Direction (Non-prescriptive)

Both entry points require the same Hartley normalization behavior.
A maintainable solution avoids duplicating that normalization logic in multiple places.
The case does not prescribe helper names or signatures; any internal organization is acceptable as long as it:
- keeps m1 behavior stable while adding m2, and
- avoids copy/paste duplication of the normalization procedure.

---

## 6. Evaluation Criteria

### 6.1 Functional

- All existing tests must pass.
- All newly introduced tests must pass.

Correctness is measured by **epipolar residuals**, not exact matrix equality (scale/sign may vary):

- Fundamental: for homogeneous pixel points `x1, x2`, residual `|x2^T F x1|` must be small on average.
- Essential: using normalized camera coordinates `x1n = K1^{-1} x1`, `x2n = K2^{-1} x2`, residual `|x2n^T E x1n|` must be small on average.

Thresholds are deterministic and fixed in `evaluator/002.refactor-and-reuse/tests/`.

### 6.2 Structural (Maintainability)

For milestone 2, the evaluator enforces a duplication constraint within `src/geometry.cc`:

- The Hartley normalization procedure must not appear as a duplicated copy inside both
  `EstimateFundamental8Point` and `EstimateEssential8Point`.
- The evaluator performs a static scan (brace-matched function-body extraction) and checks for
  a small set of normalization “fingerprints” (centroid/mean computation, √2 scaling, and similarity-transform terms).
- If the normalization fingerprints exceed a threshold in **both** function bodies, the solution fails this check.

This check is intentionally **name-agnostic**: it does not require any specific helper function name/signature.

### 6.3 Design / Constraints

- Do not change the public API in `src/geometry.h`.
- Do not change JSON I/O behavior in `app/main.cc`.
- Use braces `{}` for all `if` statements (even single-line bodies).

---

## 7. Failure Modes (Non-scoring)

Common incorrect solutions include:
- Copy/pasting Hartley normalization logic into both functions (fails the duplication check).
- Changing the public API types/signatures in `geometry.h` (breaks compilation/tests).
- Returning an unnormalized 8-point estimate without rank-2 enforcement (large residuals).
- Computing `E = K2^T F K1` but not enforcing essential singular-value constraints (large residuals).
- Hardcoding outputs or using dataset-specific constants (fails on multiple datasets).

---

## 8. Principle Mapping

```text
Mapping: NITR (not SOLID-mapped)
Measured Capability:
  - Ability to evolve code across milestones while controlling duplication
  - Ability to share an internal numeric step across features without being told a helper API
```

---

## 9. Allowed & Disallowed Summary

| Action                         | Allowed |
|--------------------------------|---------|
| Add new files                  | No      |
| Modify existing core logic     | Yes (src/geometry.cc only) |
| Modify existing tests          | No      |
| Add new dependencies           | No      |
| Use reflection / RTTI          | No      |
