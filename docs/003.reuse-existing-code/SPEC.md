---
case_id: nitr-reuse-existing-step
domain: utils
principle: SRP
difficulty: easy
language: C++
loc: ~200
---

## 1. Problem Context

This repository contains a small numeric utilities layer (`src/*`) that is reused across multiple algorithms.
A new algorithm function `solid::case003::CosineSimilarity` is being added.
In this codebase, duplicated math code is a frequent source of subtle bugs and inconsistent behavior.
The goal is to implement the algorithm while reusing the existing utility functions instead of re-implementing them.

## 2. Given Code

- `src/dot_product.*` implements `solid::case003::DotProduct(a, b)`.
- `src/l2_norm.*` implements `solid::case003::L2Norm(v)`.
- `src/cosine_similarity.cc` contains a **stub** for `solid::case003::CosineSimilarity`.
- All code compiles, but functional tests fail until the stub is implemented.

## 3. Task Description

Implement `solid::case003::CosineSimilarity(std::span<const double> a, std::span<const double> b)`.

Functional requirements:
- Throw `std::invalid_argument` if `a.size() != b.size()`.
- Return `0.0` if either vector has zero L2 norm.
- Otherwise return: `DotProduct(a, b) / (L2Norm(a) * L2Norm(b))`.

Structural constraints (must follow):
- You **MUST** reuse:
  - `solid::case003::DotProduct` from `src/dot_product.*`
  - `solid::case003::L2Norm` from `src/l2_norm.*`
- You **MUST NOT** re-implement dot product or L2 norm logic inside `src/cosine_similarity.cc`.
- You **MUST NOT** modify other files under `src/*`.
- You may add includes and small validation logic, but keep the implementation localized to `src/cosine_similarity.cc`.

## 4. Expected Design Direction (Non-prescriptive)

Acceptable solutions typically:
- Treat `CosineSimilarity` as orchestration: validate inputs, call shared primitives, and combine results.
- Keep numerical primitives centralized in `src/*` so later algorithms remain consistent.

## 5. Evaluation Criteria

### 5.1 Functional
- `evaluator/003.reuse-existing-code/tests/test_cosine_similarity.cc` must pass.

### 5.2 Structural
- `evaluator/003.reuse-existing-code/pipeline.json` enforces the structural rule
  through pipeline modules:
  - `src/cosine_similarity.cc` includes and calls `solid::case003::DotProduct` and `solid::case003::L2Norm` (or unqualified calls within the same namespace).
  - Heuristics flag likely duplicated implementations (e.g., direct `sqrt(...)` or manual accumulator patterns).

### 5.3 Design
- The implementation should be small and readable.
- No extra utility copies or alternative implementations in other files.

## 6. Failure Modes (Non-scoring)

- Re-implementing dot product / L2 norm loops in `CosineSimilarity`.
- Copy-pasting `L2Norm` or `DotProduct` into new helper functions.
- Modifying `src/*` to “fit” the new function instead of reusing them.

## 7. Principle Mapping

Violated Principle: Single Responsibility Principle (pragmatic interpretation for this case suite)

Measured Capability:
- Ability to recognize and reuse existing primitives instead of duplicating logic inside a higher-level algorithm function.
- Keeping responsibilities separated: primitives in `src/*`, orchestration in `src/cosine_similarity.cc`.

## 8. Allowed & Disallowed Summary

| Action                                   | Allowed |
|------------------------------------------|---------|
| Add new files                             | No      |
| Modify `src/cosine_similarity.cc`         | Yes     |
| Modify other `src/*` files               | No      |
| Modify existing tests                     | No      |
| Add new dependencies                      | No      |
| Re-implement dot product / L2 norm logic  | No      |
| Call `solid::case003::DotProduct` / `solid::case003::L2Norm`  | Yes     |
