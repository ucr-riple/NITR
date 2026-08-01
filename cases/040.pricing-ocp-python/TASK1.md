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
