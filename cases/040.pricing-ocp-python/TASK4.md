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
