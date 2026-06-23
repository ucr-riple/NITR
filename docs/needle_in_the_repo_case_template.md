# Needle in the Repo Case Template (v2.0)

This document defines the **mandatory structure** for all cases in **Needle in the Repo**.

The NITR case suite targets **maintainability failures in AI-generated code**, not only SOLID principle violations.
Each case should isolate a small, concrete maintainability stressor and enable objective evaluation.

All cases **must strictly follow** this template to ensure:
- consistency across domains
- clear separation between human-facing and agent-facing task descriptions
- objective and automatable evaluation
- long-term extensibility of the case suite

---

## 1. Directory Structure

Each case must use the following structure:

```text
- cases
  - <case-id>.<case-name>
    - app
      - main.<ext>
    - src
    - SPEC.md
    - TASK.md
    - CMakeLists.txt
- evaluator
  - <case-id>.<case-name>
    - checks
    - data
    - tests
```

All code and documentation must be written in **English**.
Cases may be written in **C++** or **Python**.
Case numbering must use a three-digit prefix starting from `001`.

---

## 2. SPEC.md and TASK.md Roles

### SPEC.md
`SPEC.md` is the **human-facing specification**.
It explains the case intent, maintainability target, design expectations, evaluation criteria, and common failure modes.

### TASK.md
`TASK.md` is the **agent-facing task description**.
It must be a **short section extracted from SPEC.md**.
It should contain only the information needed to complete the programming task.

### Required relationship
- `SPEC.md` **must include** the full text of `TASK.md` as one of its sections.
- `TASK.md` must be a **strict subset** of `SPEC.md`.
- `TASK.md` must **not** reveal the evaluation purpose, case-suite taxonomy, maintainability target, oracle logic, or intended failure mode.
- `TASK.md` should read like a normal engineering request, not like an evaluation prompt.

---

## 3. Case Metadata

Include the following metadata in `SPEC.md`:

```yaml
case_id:              # e.g. 009-clock-injection
title:                # short human-readable title
primary_dimension:    # one primary maintainability dimension
secondary_dimensions: # optional list
language:             # e.g. C++ | Python
granularity:          # micro | multi-step
paired_with:          # optional paired-port slug
difficulty:           # easy | medium | hard
loc:                  # approximate lines of code in starter code
```

Examples of `primary_dimension`:
- change_locality
- reuse
- extensibility
- responsibility_separation
- dependency_control
- testability
- side_effect_containment
- state_lifecycle
- error_handling_structure
- api_stability
- configuration_growth

A case should have **one primary dimension** and may have supporting secondary dimensions.

---

## 4. Problem Context

Describe the engineering background of the system in **no more than 5 lines**.

Guidelines:
- Focus on the product or engineering scenario
- Do not mention case-suite goals
- Do not mention maintainability dimensions explicitly in the narrative
- Assume a technically literate reader unfamiliar with the specific subsystem

---

## 5. Given Code

Describe the initial code state provided to the participant.

Requirements:
- The code **must build or run under the repository's configured evaluator flow**
- All provided tests **must pass**
- The initial design should contain the specific pressure point needed for the case
- The case should remain small and targeted

Include only minimal code snippets if necessary.

---

## 6. TASK.md Section (Agent-Facing)

This section appears in both `SPEC.md` and `TASK.md`.

### Writing rules for TASK.md
- Keep it short
- State only the engineering task to complete
- Mention concrete functional requirements and hard constraints
- Do not mention evaluation logic
- Do not mention maintainability dimensions
- Do not hint at the “right design lesson”
- Do not include phrases such as “this case tests whether…” or “the goal is to evaluate…”

### Recommended TASK.md structure

```md
## Task

<1-2 paragraph concise engineering request>

### Requirements
- <required behavior>
- <required behavior>
- <explicit constraint>

### Constraints
- Do not modify <files/functions>
- You may add new files under <path>
- Keep existing behavior unchanged unless required above
```

`TASK.md` should usually fit on roughly **half a page to one page**.

---

## 7. Expected Design Direction (Human-Facing, Non-prescriptive)

Describe acceptable high-level design directions in `SPEC.md` only.

Rules:
- Do not prescribe a single solution
- Do not specify exact class names or file structures unless necessary
- Focus on architectural intent
- Describe what kinds of change patterns are desirable or undesirable

This section must **not** be copied into `TASK.md`.

---

## 8. Evaluation Criteria

Evaluation is described in `SPEC.md` only.

### 8.1 Functional
- All existing tests must pass
- All newly introduced tests must pass
- The requested behavior must be implemented correctly

### 8.2 Structural
- File-level, class-level, or function-level constraints
- Forbidden modification regions
- Forbidden patterns if applicable

### 8.3 Maintainability
- Locality of change
- Dependency structure
- Reuse of existing code
- Side-effect isolation
- Interface stability
- Test seam quality
- Other case-specific maintainability signals

---

## 9. Oracle Signals

List the concrete signals used by the evaluator.
These may include:
- tests
- static checks
- grep-based checks
- include dependency checks
- file modification checks
- symbol usage checks
- registration or wiring checks

This section is for humans and case authors.
It must **not** appear in `TASK.md`.

---

## 10. Failure Modes (Non-scoring)

List common incorrect or degenerate solutions.

Examples:
- implements the feature by patching multiple call sites
- duplicates existing logic instead of reusing repo code
- introduces global mutable state
- mixes IO or logging into core domain logic
- widens a public API unnecessarily

These are for qualitative analysis and discussion.
They are not part of the agent-facing task statement.

---

## 11. Maintainability Mapping

Explain how the case maps to the NITR taxonomy.

Recommended format:

```text
Primary Dimension:
  - <dimension>
Measured Capability:
  - <capability 1>
  - <capability 2>
Secondary Dimensions:
  - <optional>
```

This section replaces older SOLID-only mappings.
A case may be inspired by SOLID, but it does not need to target a SOLID principle.

---

## 12. Allowed & Disallowed Summary

Include a summary table in `SPEC.md`:

| Action                         | Allowed |
|--------------------------------|---------|
| Add new files                  |         |
| Modify existing core logic     |         |
| Modify existing tests          |         |
| Add new dependencies           |         |
| Modify public headers          |         |
| Use global mutable state       |         |
| Introduce new external IO      |         |

---

## 13. Authoring Rules

- Each case must isolate one **primary maintainability dimension**
- Cases should stay small and targeted
- `TASK.md` must remain concise and non-revealing
- `SPEC.md` should be sufficient for human review and case maintenance
- Non-conforming cases should not be merged
- Template changes require version updates
