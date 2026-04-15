# Needle in the Repo: Design Matrix (D1-D9)

This document records the current maintainability design matrix for **Needle in the Repo**.
The NITR case suite is organized around **nine maintainability dimensions (D1-D9)** rather than a SOLID-only taxonomy.
Each case should declare exactly one **primary dimension**.

## Design goals

Needle in the Repo is designed around four goals:

1. **Maintainability-first evaluation**: measure structural quality beyond functional correctness.
2. **Small, diagnosable probes**: each case isolates one primary maintainability failure mode.
3. **Natural agent-facing tasks**: `TASK.md` stays short and does not reveal evaluation intent.
4. **Balanced coverage**: cover the major maintainability failure modes with a mix of micro and multi-step cases.

---

## D1. Change Locality

Measures whether a small requirement change remains local or spreads unnecessarily across callsites, signatures, or public interfaces.

Typical failures:
- callsite spread
- change amplification
- signature churn
- unnecessary public API expansion

Current cases:
- `001 add-no-callsite-spread`
- `011 config-sprawl`
- `013 stable-public-api`

Current count: **3**

---

## D2. Reuse and Repo Awareness

Measures whether the agent recognizes and reuses existing code, abstractions, and helpers in the repository instead of reimplementing or bypassing them.

Typical failures:
- duplicate implementation
- parallel helper creation
- bypassing existing repo affordances
- reimplementation instead of reuse

Current cases:
- `002 refactor-and-reuse`
- `003 reuse-exising-code`
- `021 inline-filter-entrypoint-reuse` (**micro**)

Current count: **3**

Notes:
- `021` is the D2 micro case that completes the previously missing D2 coverage slot.
- Its pressure point is convergence into the repository's existing structured parse/validate path rather than introducing a shadow inline parser.

---

## D3. Responsibility Decomposition

Measures whether responsibilities remain cleanly separated and whether new requirements preserve module boundaries.

Typical failures:
- mixed concerns
- orchestration logic inside core logic
- parsing/rendering mixed with domain logic
- cross-cutting concerns leaking into core modules

Current cases:
- `004 cv-srp`
- `020 handover-packet-ownership-boundary` (**micro**)

Current count: **2**

Notes:
- `020` is the newly added D3 micro case.
- Replace the temporary slug once the final case title is fixed.

---

## D4. Extension Structure

Measures whether new behavior is added by extension or by patching existing central logic.

Typical failures:
- giant switch growth
- repeated edits to central dispatch logic
- fragile type-code branching
- extension through patching rather than localized addition

Current cases:
- `005 pricing-ocp`
- `014 report-export-ocp`

Current count: **2**

---

## D5. Interface and Substitutability Discipline

Measures whether interfaces remain minimal and whether substitutable implementations preserve a shared contract across callers and execution modes.

Typical failures:
- bloated interfaces
- subtype-specific caller branching
- concrete-only methods leaking upward
- substitutability that works only in one narrow use path

Current cases:
- `006 gs-isp` (**micro**)
- `007 ml-lsp` (**upgraded to multi-step**)

Current count: **2**

Notes:
- `006` remains a micro probe.
- `007` is the D5 multi-step case.

---

## D6. Dependency Control

Measures whether high-level logic remains decoupled from concrete implementations and environmental details.

Typical failures:
- direct dependency on filesystem, clock, randomness, or specific providers
- hidden concrete coupling
- hard-coded collaborators
- seams that exist only superficially and do not support later extension

Current cases:
- `008 map-dip`
- `015 pipeline-provider-decoupling`
- `022 thermostat-sensor-decoupling`

Current count: **3**

---

## D7. Testability and Determinism

Measures whether the resulting code supports fast, deterministic, low-friction testing without relying on real time, sleep, or awkward inspection paths.

Typical failures:
- sleep-based tests
- hidden wall clock dependency
- hidden nondeterminism
- brittle boundary-condition testing
- dependence on real environment behavior

Current cases:
- `009 session-expiry-testability`
- `018 seeded-selection-testability` (**multi-step**)

Current count: **2**

---

## D8. State Ownership and Lifecycle

Measures whether mutable state has clear ownership and whether reset, invalidate, refresh, or replacement rules remain localized and understandable.

Typical failures:
- hidden shared mutable state
- unclear ownership of caches or buffers
- reset/invalidate logic scattered across the codebase
- lifecycle control leaking into unrelated APIs

Current cases:
- `012 cache-lifecycle`
- `017 active-snapshot-lifecycle` (**multi-step**)

Current count: **2**

---

## D9. Side-Effect Isolation

Measures whether logging, metrics, IO, tracing, and other side effects remain localized instead of intruding into core decision logic.

Typical failures:
- logging inside core policy logic
- metrics or tracing mixed into core algorithms
- intrusive hooks in otherwise pure logic
- cross-cutting concerns scattered across multiple core modules
- explanation / inspection concerns contaminating ranking or comparison paths

Current cases:
- `010 logging-side-effects`
- `019 ranking-explainability-boundary` (**multi-step**)

Current count: **2**

Notes:
- `010` remains the micro side-effect probe.
- `019` is the D9 multi-step case focused on explainability / inspection pressure without collapsing into a logging-only task.

---

## Current primary-dimension assignment

| Case | Primary dimension | Granularity |
|---|---|---|
| 001 add-no-callsite-spread | D1 Change Locality | multi-step |
| 002 refactor-and-reuse | D2 Reuse and Repo Awareness | multi-step |
| 003 reuse-exising-code | D2 Reuse and Repo Awareness | multi-step |
| 004 cv-srp | D3 Responsibility Decomposition | multi-step |
| 005 pricing-ocp | D4 Extension Structure | multi-step |
| 006 gs-isp | D5 Interface and Substitutability Discipline | micro |
| 007 ml-lsp | D5 Interface and Substitutability Discipline | multi-step |
| 008 map-dip | D6 Dependency Control | micro |
| 009 session-expiry-testability | D7 Testability and Determinism | micro |
| 010 logging-side-effects | D9 Side-Effect Isolation | micro |
| 011 config-sprawl | D1 Change Locality | micro |
| 012 cache-lifecycle | D8 State Ownership and Lifecycle | micro |
| 013 stable-public-api | D1 Change Locality | micro |
| 014 report-export-ocp | D4 Extension Structure | micro |
| 015 pipeline-provider-decoupling | D6 Dependency Control | multi-step |
| 016 device-segment-planner | D7 Testability and Determinism | multi-step |
| 017 active-snapshot-lifecycle | D8 State Ownership and Lifecycle | multi-step |
| 018 seeded-selection-testability | D7 Testability and Determinism | multi-step |
| 019 ranking-explainability-boundary | D9 Side-Effect Isolation | multi-step |
| 020 handover-packet-ownership-boundary | D3 Responsibility Decomposition | micro |
| 021 inline-filter-entrypoint-reuse | D2 Reuse and Repo Awareness | micro |
| 022 thermostat-sensor-decoupling | D6 Dependency Control | micro |

---

## Coverage snapshot

| Dimension | Count |
|---|---:|
| D1 Change Locality | 3 |
| D2 Reuse and Repo Awareness | 3 |
| D3 Responsibility Decomposition | 2 |
| D4 Extension Structure | 2 |
| D5 Interface and Substitutability Discipline | 2 |
| D6 Dependency Control | 3 |
| D7 Testability and Determinism | 3 |
| D8 State Ownership and Lifecycle | 2 |
| D9 Side-Effect Isolation | 2 |

Total cases recorded: **22**

Notes:
- Current matrix contents cover cases `001`-`022`.
- With `021` and `016` included, D1, D2, and D7 each have three cases; D3-D6 and D8-D9 each have two.
