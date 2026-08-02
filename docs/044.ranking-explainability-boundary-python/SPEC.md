---
case_id: 044-ranking-explainability-boundary-python
title: Ranking Explainability Boundary, Python
primary_dimension: side_effect_isolation
secondary_dimensions: []
language: Python
granularity: multi-step
paired_with: 019.ranking-explainability-boundary
difficulty: medium
loc: ~180-260
---

# Case 044: Ranking Explainability Boundary, Python

## Problem context

A deterministic ranking engine scores eligible items and excludes blocked
candidates. Product and support callers now need compact reasons, targeted
inspection, and pairwise comparison without turning the ordinary ranking path
into a display, logging, or diagnostic payload producer.

## Case metadata and matrix rationale

- Primary dimension: `D9 Side-Effect Isolation`
- Granularity: `multi-step`
- Paired with: `019.ranking-explainability-boundary`
- Difficulty: `medium`

This Python port retains the cumulative pressure on result shape and observer
features. The evaluator permits one compact reason summary but rejects
inspection/comparison state in normal ranked results and output side effects in
the decision core.

## Given code

The starter contains `Item`, compact `RankedItem`, and a complete `Ranker` with
blocked exclusion, score adjustments, and deterministic score/base-score/id
ordering. Explainability and inspection modules are intentionally absent.

## Agent-facing contract

The following sections reproduce all three task files in full.

## Task 1

## Task

Extend ranked results so they include a compact structured reason summary for each returned item.

### Requirements
- Keep the existing ranking rules and output order unchanged unless a requirement below adds new returned data.
- For each ranked item, return a compact structured reason summary that includes:
  - the final score
  - the strongest positive factor that helped the item
  - the strongest negative factor, if any
- Keep the implementation deterministic.

### Constraints
- Do not remove existing ranking behavior.
- Do not turn this into a logging or tracing feature.
- You may add new files under `src/` and update `app/main.py` if needed.
- Keep the codebase small and do not add external dependencies.

## Task 2

## Task

Add a targeted inspection capability for a single candidate in the same ranking engine.

### Requirements
- Keep the ranked-result reason summary working.
- Add an inspection capability that takes the same candidate set plus a candidate id and returns enough information to tell whether that candidate was:
  - excluded before ranking
  - included but ranked lower because of score adjustments
  - ordered behind another candidate because of the tie-break rules
- If a candidate id is unknown, return a clear not-found result.
- The inspection output should be structured data, not free-form paragraphs.

### Constraints
- Do not remove existing ranking behavior.
- Do not turn this into a logging or tracing feature.
- You may add new files under `src/` and update `app/main.py` if needed.
- Keep the implementation deterministic.
- Keep the codebase small and do not add external dependencies.

## Task 3

## Task

Finish the explainability feature by adding a comparison capability for two ranked candidates.

### Requirements
- Keep the ranked-result reason summary and single-candidate inspection capability working.
- Add a comparison capability for two candidates that are both present in the ranked result.
- The comparison output should explain why one ranked above the other using the existing score and tie-break rules.
- If the comparison request references a candidate that is not in the ranked result, return a clear unsupported or not-applicable result.
- The output should be structured data, not free-form paragraphs.

### Constraints
- Do not remove existing ranking behavior.
- Do not turn this into a logging or tracing feature.
- You may add new files under `src/` and update `app/main.py` if needed.
- Keep the implementation deterministic.
- Keep the codebase small and do not add external dependencies.

## Expected design direction (human-facing)

Keep scoring facts structured and share one scoring authority between ranking
and observers. A normal `RankedItem` may carry one compact reason summary.
Blocked inspection and pairwise comparison should use targeted result types
outside the default ranking result rather than widening it for niche consumers.

## Hidden evaluator intent

This D9 case measures whether observer-facing requirements contaminate ranking
decisions. Functionally correct solutions are rejected if they add logging,
display text, or broad inspection/comparison bookkeeping to the ordinary
ranking path.

## Functional expectations

- baseline order and scores remain unchanged
- summaries identify final score and strongest positive/negative factors
- blocked, ranked, tie-loss, and missing inspection states are structured
- comparison distinguishes final-score and tie-break decisions
- comparison involving blocked/missing candidates is not applicable
- ranking emits no stdout or stderr

## Evaluator plan

### Functional checks

Tests lock baseline scores, summaries for positive and negative examples,
blocked/missing inspection, tie-break inspection, supported and unsupported
comparison, determinism, and absence of output side effects.

### Structural / oracle checks

AST analysis rejects print/log calls and executable explanation-oriented
literals in the ranking core while allowing ordinary docstrings and string
annotations. It limits `RankedItem` to three fields and explicitly rejects
inspection/comparison fields such as status, tie opponent, winner, loser, and
decisive reason from the default result.

## Failure modes (non-scoring)

- assembling explanation paragraphs inside score or sort branches
- printing, logging, or tracing ranking decisions
- adding blocked-candidate and comparison payloads to every ranked item
- duplicating scoring interpretation in observer-specific code
- changing baseline ordering while adding explanations
- threading pairwise comparison bookkeeping through the sort path

## Maintainability mapping

Primary Dimension:

- D9 Side-Effect Isolation

Measured Capability:

- keep observer concerns outside the ranking decision path
- expose compact structured reasons without default-result inflation
- localize targeted inspection and comparison state

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Modify ranking source | Yes |
| Add focused source modules | Yes |
| Add one compact reason summary to `RankedItem` | Yes |
| Add external dependencies | No |
| Add logging/tracing to ranking | No |
| Add inspection/comparison fields to `RankedItem` | No |
| Modify evaluator files | No |
