# 006 - Tiny GS Render Data Views (ISP)

## 1. Case Metadata

```yaml
case_id: graphics-ISP-gs_render_views
domain: graphics
principle: ISP
difficulty: easy
language: C++
loc: ~220
```

## 2. Problem Context

A lightweight Gaussian Splatting renderer is used in a graphics toolchain for debugging and regression tests.
Its tiny render path has four stages: project/bin, per-tile depth sort, SH-based shading, and alpha compositing.
The current implementation works functionally, but the stage boundaries are too wide.
Downstream tools that only need sorting or compositing still depend on the full hit representation.
The team wants narrower stage-specific data interfaces without changing rendering behavior.

## 3. Given Code

The provided code compiles and the public smoke test passes.
The render pipeline already has four explicit stages:
- `ProjectAndBin`
- `SortHitsByTileThenDepth`
- `EvalShading`
- `CompositeToImage`

The design clearly violates Interface Segregation Principle because all stages directly consume the legacy `HitBuffer` and `Hit` definitions from `src/hit_buffer.h`, even when a stage only needs a very small subset of fields.

## 4. Task Description

Refactor the stage boundaries so that sorting, shading, and compositing use stage-specific data views instead of depending directly on the legacy `HitBuffer` type.

Required outcome:
- keep the four-stage pipeline behavior unchanged
- introduce narrow interfaces / views for at least:
  - sorting
  - shading
  - compositing
- update the stage APIs so that these stages no longer expose `HitBuffer` in their public headers

Constraints:
- do **not** modify `app/main.cc`
- do **not** modify `evaluator/006.gs-isp/tests/test_public_smoke.cc`
- do **not** add third-party dependencies
- do **not** use RTTI, reflection, or type-switching on concrete classes
- you may add new files, wrappers, adapters, or view classes
- you may keep `src/hit_buffer.h` as a legacy storage type if desired, but stage-specific headers must not depend on it directly

## 5. Expected Design Direction (Non-prescriptive)

Acceptable solutions should narrow each stage to the minimal data it actually needs.
This can be achieved with interface classes, lightweight views, adapters over legacy storage, or other forms of boundary reduction.
The key goal is that each stage depends only on its own required slice of the hit data rather than the entire storage representation.

## 6. Evaluation Criteria

### 6.1 Functional
- All existing tests must pass
- Rendering output checksum must remain unchanged for the public test scene

### 6.2 Structural
- `src/sort_hits.h` must not expose `HitBuffer` or `Hit`
- `src/eval_shading.h` must not expose `HitBuffer`
- `src/composite.h` must not expose `HitBuffer`
- `sort_hits.cc`, `eval_shading.cc`, and `composite.cc` must not include `hit_buffer.h` directly
- No RTTI or reflection

### 6.3 Design
- The solution must introduce narrow stage-specific views or interfaces
- Sorting must depend only on sortable hit information
- Shading must depend only on shading-relevant hit information
- Compositing must depend only on compositing-relevant hit information
- Legacy storage may remain internal, but not as the public dependency surface of all stages

## 7. Failure Modes (Non-scoring)

Common weak solutions include:
- keeping `HitBuffer` in all public stage signatures and only renaming types
- introducing one new wrapper that still exposes every field to every stage
- moving all logic into a single pipeline class to hide the dependency problem
- using dynamic casts or concrete-type checks instead of narrowing interfaces
- changing rendering math and accidentally breaking deterministic output

## 8. Principle Mapping

Violated Principle: Interface Segregation Principle
Measured Capability:
  - Ability to narrow data dependencies at stage boundaries
  - Ability to introduce minimal, role-specific interfaces over legacy storage
  - Ability to preserve behavior while reducing unnecessary coupling

## 9. Allowed & Disallowed Summary

| Action                         | Allowed |
|--------------------------------|---------|
| Add new files                  | Yes     |
| Modify existing core logic     | Yes, if behavior is preserved |
| Modify existing tests          | No      |
| Add new dependencies           | No      |
| Use reflection / RTTI          | No      |
