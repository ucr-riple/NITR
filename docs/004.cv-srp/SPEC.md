# SPEC: SOLIDbench Case — computer_vision-SRP-feature_model_estimation

## 1. Case Metadata

```yaml
case_id:        computer_vision-SRP-feature_model_estimation
domain:         computer_vision
principle:      SRP
difficulty:     medium
language:       C++
loc:            500-900
task_style:     hybrid (legacy reference + SRP pipeline implementation)
```

---

## 2. Problem Context

You are maintaining a lightweight 2-view geometric front-end used in a tracking/VO pipeline.
Given two frames’ 2D keypoints and a list of matches, the system estimates a geometric model
(Essential matrix `E` for calibrated motion), produces an inlier mask, computes quality metrics,
and makes an ACCEPT/REJECT decision.

The repository contains a **legacy monolithic reference implementation** that is correct but violates SRP.
Your task is to implement an SRP-compliant pipeline that **matches the legacy behavior** on provided cases,
while keeping module boundaries enforceable by static checks.

---

## 3. Repository Layout (Required)

This case follows the current repository layout used in NITR:

```text
cases/004.cv-srp/
  CMakeLists.txt
  TASK1.md
  TASK2.md
  TASK3.md
  app/
    main.cc
  src/
    types.h
    io_json.h
    io_json.cc
    normalize.h
    normalize.cc
    estimator.h
    estimator_e.cc
    scoring.h
    scoring.cc
    policy.h
    policy.cc
    pipeline.h
    pipeline.cc
    legacy_monolith.h
    legacy_monolith.cc

evaluator/004.cv-srp/
  checks/
    check.py
  data/
    simple_ok.json
    invalid_schema.json
    reject_case.json
    estimation_failed.json
    outlier_mix.json
  tests/
    test_io_json.cc
    test_scoring.cc
    test_policy.cc
    test_pipeline.cc
```

Intent:
- `app/` contains the executable entrypoint and CLI wiring only.
- `src/` contains all implementation code; SRP boundaries apply here.
- `src/legacy_monolith.*` is a **behavior reference** (oracle), not the target architecture.
- `evaluator/004.cv-srp/` contains black-box data, static checks, and unit tests.

---

## 4. Given Code (Hybrid Starter)

The starter repository contains:

1) **Legacy reference implementation** (`src/legacy_monolith.cc`)
- Implements the full end-to-end behavior (parse → normalize → estimate → score → decide → serialize)
- Passes all functional expectations on the provided test cases
- Violates SRP by mixing responsibilities

2) **SRP pipeline skeleton** (`src/pipeline.*` and component files in `src/`)
- Exists but is incomplete and/or incorrectly wired
- Must be completed so that the final executable behavior matches the legacy reference

### Rules for the legacy reference
- `src/legacy_monolith.cc` MUST NOT be modified.
- The SRP pipeline MUST NOT call into `legacy_monolith` at runtime for normal execution.
  (The harness may call the legacy path for comparison; production path must be SRP pipeline.)

---

## 5. Task Description (Hybrid)

Implement the SRP-compliant pipeline so that:

- `cv_srp` uses the SRP pipeline by default
- Outputs (including error handling) match the legacy reference on all provided data cases
- SRP boundaries are respected and enforced by static checks
- cv_srp must not link legacy; legacy is only linked into dedicated oracle regression tests in evaluator tests.
- SRP pipeline must not include or call legacy APIs.

This is **not** a pure refactor: you are not asked to reshape the legacy monolith.
Instead, you are asked to implement the new SRP pipeline while using the legacy code only as an oracle.

---

## 6. Required Behavior

### CLI
- Binary: `cv_srp`
- Usage: `cv_srp --input <pair.json> --output <result.json>`

### Exit codes
- `0`: success (ACCEPT)
- `2`: invalid input JSON or schema
- `3`: estimation failed (no model could be produced)
- `4`: rejected by policy (REJECT)

On error, print exactly one line to stderr:
- `ERR_INVALID_JSON`
- `ERR_INVALID_SCHEMA`
- `ERR_ESTIMATION_FAILED`
- `ERR_REJECTED`

---

## 7. Input / Output

### Input: `pair.json`

Schema:
```json
{
  "camera": { "fx": 525.0, "fy": 525.0, "cx": 319.5, "cy": 239.5 },
  "frame0": { "keypoints": [[x,y], ...] },
  "frame1": { "keypoints": [[x,y], ...] },
  "matches": [[i0, i1], ...],
  "options": {
    "model": "E",
    "ransac_thresh_px": 1.5,
    "max_iters": 2000,
    "seed": 12648430
  }
}
```

Constraints:
- `fx, fy > 0`
- keypoints non-empty
- matches indices must be in range
- `ransac_thresh_px > 0`
- `max_iters` in `[1, 1e7]`
- `model` is `"E"` (this case is E-only)

### Output: `result.json`

```json
{
  "model": "E",
  "params": { "E": [[...],[...],[...]] },
  "inliers": [true, false, ...],
  "metrics": {
    "num_matches": 120,
    "num_inliers": 85,
    "inlier_ratio": 0.7083,
    "median_sampson_error": 0.42
  },
  "decision": "ACCEPT"
}
```

Definitions:
- `inliers` length must equal `num_matches` and align with `matches` order.
- `median_sampson_error` is computed on **normalized coordinates**.

---

## 8. SRP Design Requirements

Minimum conceptual components (names are not prescribed):
1. **Parser/Schema validation** (JSON → domain structs)
2. **Normalization** (pixel → normalized coordinates)
3. **Model estimation** (RANSAC Essential matrix estimation)
4. **Quality scoring** (compute metrics from estimation result)
5. **Decision policy** (thresholding logic only)
6. **Serializer** (domain result → JSON)

### Hard constraints (must NOT be violated)
- Estimation code must NOT parse/serialize JSON.
- Estimation code must NOT apply accept/reject thresholds.
- Scoring code must NOT run estimation or modify inlier masks.
- Policy code must NOT recompute residuals from scratch; it consumes metrics only.
- SRP pipeline must not call `legacy_monolith` for normal execution.

---

## 9. Evaluation Criteria

### 9.1 Functional
- All existing tests must pass.
- The case-provided tests will verify:
  - SRP pipeline output matches legacy reference on `evaluator/004.cv-srp/data/*.json`
  - invalid schema triggers correct error code + stderr string
  - deterministic behavior given a fixed `seed`
  - reject path produces decision=REJECT and exit code 4

### 9.2 Structural (Static SRP Checks)

Enforced by `evaluator/004.cv-srp/checks/check.py` via include- and symbol-usage checks.

**JSON usage restrictions**
- `src/estimator_*.cc` must NOT include `nlohmann/json.hpp` and must NOT include `src/io_json.h`
- `src/scoring.cc` must NOT include `nlohmann/json.hpp` and must NOT include `src/io_json.h`
- `src/policy.cc` must NOT include `nlohmann/json.hpp` and must NOT include `src/io_json.h`

**Dependency restrictions**
- `src/policy.cc` must NOT include `src/normalize.h` or any `src/estimator*.h`
  (policy consumes metrics only)
- Only the composition root (`app/main.cc` and/or `src/pipeline.cc`) may include both:
  - IO + normalization + estimation + scoring + policy

**Legacy isolation**
- No source file under `src/` (except `legacy_monolith.*`) may include `legacy_monolith.h`

Forbidden patterns:
- A single function/class that performs 3+ responsibilities (parse + estimate + score + decide + serialize)
- Decision logic embedded in estimator (e.g., estimator returning “rejected”)
- Policy re-implementing geometric residual computations

---

## 10. Failure Modes (Non-scoring)

Common incorrect solutions:
- Calling `legacy_monolith` from the SRP pipeline (cheating).
- Moving JSON parsing into estimator “for convenience”.
- Computing `median_sampson_error` inside estimator and returning it as “metrics”.
- Policy re-evaluates residuals directly by re-implementing the error computation.
- Keeping a “Pipeline” class that still does everything internally.

---

## 11. Principle Mapping

```text
Violated Principle: Single Responsibility Principle (SRP)

Measured Capability:
  - Ability to separate IO, normalization, estimation, scoring, and decision policy
  - Ability to implement a clean architecture while matching a legacy reference behavior
  - Ability to respect enforceable module boundaries via static checks
```

---

## 12. Allowed & Disallowed Summary

| Action                                      | Allowed |
|---------------------------------------------|---------|
| Add new files                               | Yes     |
| Modify SRP pipeline code under `src/`       | Yes     |
| Modify `src/legacy_monolith.*`              | No      |
| Modify tests under `evaluator/004.cv-srp/tests`        | No      |
| Add new dependencies                        | No (beyond what starter provides) |
| Use reflection / RTTI                       | No      |
