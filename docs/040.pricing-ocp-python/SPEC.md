---
case_id: 040-pricing-ocp-python
title: Pricing OCP, Python
primary_dimension: extension
secondary_dimensions: []
language: Python
granularity: multi-step
paired_with: 005.pricing-ocp
difficulty: hard
loc: ~180-300
---

# Case 040: Pricing OCP, Python

## Problem context

A pricing CLI evolves through four milestones: built-in discounts, coupons,
selection constraints, and runtime-loaded rules. Each milestone must preserve
earlier behavior while keeping the central pricing calculation independent of
individual coupon codes and rule types.

## Case metadata and matrix rationale

- Case id / slug: `040-pricing-ocp-python`
- Title: `Pricing OCP, Python`
- Primary dimension: `D4 Extension Structure`
- Secondary dimensions: none
- Granularity: `multi-step`
- Paired with: `005.pricing-ocp`
- Difficulty: `hard`

Rationale for inclusion:

- This is the Python paired port of case `005.pricing-ocp`.
- It preserves the four-milestone pressure that repeatedly adds discount
  behavior.
- The evaluator combines behavior checks, runtime extension injection, and AST
  analysis of the pricing core's reachable helper path.

## Given code

```text
- cases/040.pricing-ocp-python/app/main.py
- cases/040.pricing-ocp-python/src/pricing.py
- cases/040.pricing-ocp-python/TASK1.md
- cases/040.pricing-ocp-python/TASK2.md
- cases/040.pricing-ocp-python/TASK3.md
- cases/040.pricing-ocp-python/TASK4.md
- cases/040.pricing-ocp-python/CMakeLists.txt
- evaluator/040.pricing-ocp-python/pipeline.json
- evaluator/040.pricing-ocp-python/tests/test_pricing.py
- evaluator/040.pricing-ocp-python/checks/run_evaluator.py
- evaluator/040.pricing-ocp-python/data/runtime_rules.json
- docs/040.pricing-ocp-python/SPEC.md
```

`src/pricing.py` supplies the order, result, rule, and registry boundaries. Its
starter calculation can evaluate externally registered rules, but none of the
built-in or runtime rule sources have been implemented. `app/main.py` is an
incomplete JSON CLI adapter.

## Input and output contract

The input JSON contains `subtotal` (finite and non-negative), `is_member`
(boolean), `items` (non-negative integer), and `coupons` (array of strings).
Duplicate coupons are treated as a set. Unknown coupons are ignored.

The result JSON contains a non-negative `final_price`, rounded to two decimal
places, and the selected rule IDs in `applied_rules`.

Each rule contributes either a percent discount in `[0.0, 1.0]` or a
non-negative flat USD discount. Let `P` be the sum of selected percentages,
clamped to `0.95`, and `F` the sum of selected flat discounts. The result is
`round(max(0, subtotal * (1 - P) - F), 2)`, with only one rounding operation at
the end.

Built-in rules are:

- `ITEMS_20OFF`: flat 20.00 when `items >= 10`
- `MEMBER_10P`: 10 percent when the order is a member order
- `COUPON_SAVE5`: flat 5.00 when the coupon set contains `SAVE5`
- `COUPON_SAVE10P`: 10 percent when it contains `SAVE10P`

Milestone `m1` uses the first two rules. `m2` adds both coupon rules. From `m3`
onward, grouped rules are exclusive: highest priority wins, then
lexicographically largest ID. Both built-in coupons use group `COUPON`, with
priorities 10 and 20 respectively. A selected rule whose `disables_member` is
true removes `MEMBER_10P`.

In `m4`, the runtime rule path is selected from `--rules`, then `NITR_RULES`,
then a current-directory `rules.json`, if present. A runtime rule has an ID,
`percent` or `flat` type, value, integer priority, optional group, optional
`disables_member`, and optional `when` conditions for coupon, membership, and
minimum items. All present conditions must match.

Selected rule IDs are ordered by group name (empty first), descending priority,
then ascending ID.

The CLI is:

```text
pricing --in <order.json> --out <result.json> --milestone <m1|m2|m3|m4> [--rules <rules.json>]
```

Failures return non-zero and print exactly one of `ERR_INVALID_JSON`,
`ERR_INVALID_SCHEMA`, `ERR_UNSUPPORTED_MILESTONE`, or `ERR_IO`.

## Agent-facing contract

The following sections reproduce the full texts of all four task files.
Internal sections after them are not exposed to the coding agent.

## Task 1

## Task

Implement the `pricing` CLI for the first milestone mode so it can read an
order JSON file, apply the built-in rules, and write the result.

### Requirements

- Support milestone `m1` with the built-in item-count and member rules.
- Implement the built-in rules needed for that first milestone mode.
- Apply the specified discount aggregation rules and round only once at the end.
- Produce deterministic `applied_rules` ordering.

### Constraints

- Keep the CLI contract as `pricing --in <order.json> --out <result.json>
  --milestone <m1|m2|m3|m4> [--rules <rules.json>]`.
- Treat `coupons` as a set for matching.
- Unknown coupon codes are allowed and simply do not match any rule.
- Do not modify evaluator files.

## Task 2

## Task

Extend the `pricing` CLI to support the second milestone mode, `m2`, by adding
the built-in coupon rules on top of the existing `m1` behavior.

### Requirements

- Keep the earlier `m1` milestone behavior working.
- Support milestone `m2`.
- Implement the built-in coupon rules needed for that second milestone mode.
- Apply the specified discount aggregation rules and round only once at the end.
- Produce deterministic `applied_rules` ordering.

### Constraints

- Keep the CLI contract as `pricing --in <order.json> --out <result.json>
  --milestone <m1|m2|m3|m4> [--rules <rules.json>]`.
- Treat `coupons` as a set for matching.
- Unknown coupon codes are allowed and simply do not match any rule.
- Do not modify evaluator files.

## Task 3

## Task

Extend the `pricing` CLI to support the third milestone mode, `m3`, with the
additional coupon interaction rules.

### Requirements

- Keep the earlier `m1` and `m2` milestone behavior working.
- Support milestone `m3`.
- In `m3`, enforce coupon-group exclusivity and `disables_member`.
- Keep deterministic `applied_rules` ordering and round only once at the end.

### Constraints

- Keep the CLI contract as `pricing --in <order.json> --out <result.json>
  --milestone <m1|m2|m3|m4> [--rules <rules.json>]`.
- Treat `coupons` as a set for matching.
- Unknown coupon codes are allowed and simply do not match any rule.
- Do not modify evaluator files.

## Task 4

## Task

Finish the `pricing` CLI by adding runtime rule loading for the fourth milestone
mode, `m4`, while keeping the earlier milestone behavior intact.

### Requirements

- Keep `m1`, `m2`, and `m3` behavior working.
- In `m4`, load runtime rules from `--rules`, `NITR_RULES`, or `rules.json` in
  the current working directory.
- Return the required error codes and stderr messages for invalid input,
  invalid rules, unsupported milestones, and IO failures.
- If a runtime rules file is present but invalid, fail with the appropriate
  rules error.

### Constraints

- Keep the CLI contract as `pricing --in <order.json> --out <result.json>
  --milestone <m1|m2|m3|m4> [--rules <rules.json>]`.
- Treat `coupons` as a set for matching.
- Unknown coupon codes are allowed and simply do not match any rule.
- Do not modify evaluator files.

## Expected design direction (human-facing)

Concrete built-in and runtime rules should implement `PricingRule` and enter
the calculation through `RuleRegistry`. The core should perform only generic
applicability, group selection, member suppression, aggregation, and ordering.
Adding a new coupon should therefore add a rule implementation or
configuration without editing a coupon-code dispatch chain in the core.

## Hidden evaluator intent

This D4 multi-step case measures whether repeated feature pressure grows an
extension seam or a central conditional. A behaviorally correct implementation
that hardcodes coupon identifiers into the pricing core is intentionally
rejected.

The runtime injection test registers an evaluator-owned `PricingRule` and
expects it to affect the result. This prevents a decorative registry that is
never used by the calculation.

## Functional expectations

- all milestone-specific built-in rules produce the specified totals
- duplicate coupons do not multiply a discount
- group priority and deterministic tiebreak selection are respected
- selected runtime rules participate in group and member-disable behavior
- invalid runtime rules fail with the required error
- unknown coupons have no effect
- an evaluator-defined rule works without pricing-core edits

## Evaluator plan

### Functional checks

Python unit tests exercise milestone behavior, aggregation, coupon set
semantics, group exclusivity, runtime loading, invalid runtime schemas, unknown
coupons, and an externally registered evaluator rule. A separate subprocess
suite executes `app/main.py` and verifies successful JSON I/O, the
`--rules`/`NITR_RULES`/current-directory precedence chain, non-zero exits, and
the exact stderr line for all four documented error categories.

### Structural / oracle checks

The AST evaluator:

- requires `compute_final_price()` to obtain candidates from
  `RuleRegistry.create_all()`
- follows module-level helpers reachable from `compute_final_price()`
- rejects coupon- or promo-specific conditionals on that reachable path
- rejects known built-in coupon and rule identifiers on that path
- allows those details inside concrete rule classes and rule factories outside
  the central orchestration path

## Failure modes (non-scoring)

- adding `if`/`elif` branches for each coupon in `compute_final_price()`
- moving the same central dispatch into a helper called by the core
- defining a registry but bypassing its rules during calculation
- duplicating coupons rather than treating them as a set
- applying group exclusivity or member disabling in coupon-specific branches
- rounding intermediate discount contributions
- silently ignoring an invalid runtime rules file

## Maintainability mapping

Primary Dimension:

- D4 Extension Structure

Measured Capability:

- extend pricing through new rules rather than central dispatch edits
- preserve a generic calculation pipeline across four feature milestones
- make repository and runtime rule additions use the same extension boundary

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Modify starter source files | Yes |
| Add rule implementation modules under `src/` | Yes |
| Modify evaluator files | No |
| Add external dependencies | No |
| Add concrete `PricingRule` implementations | Yes |
| Register built-in and runtime rules through the rule seam | Yes |
| Add coupon-specific dispatch to the pricing core path | No |
