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
