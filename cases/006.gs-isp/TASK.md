## Task Description

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
- do **not** modify `evaluator/tests/test_public_smoke.cc`
- do **not** add third-party dependencies
- do **not** use RTTI, reflection, or type-switching on concrete classes
- you may add new files, wrappers, adapters, or view classes
- you may keep `src/hit_buffer.h` as a legacy storage type if desired, but stage-specific headers must not depend on it directly