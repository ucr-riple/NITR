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
