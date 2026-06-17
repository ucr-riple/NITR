# Discount Engine (OCP) Spec

This task models a discount engine that evolves by milestones while keeping the
pricing core closed for modification and open for extension (OCP).

All I/O is JSON. Amounts are in USD.

---

## 0. Repository Layout

This case follows the current repository layout used in NITR:

```text
cases/005.pricing-ocp/
  CMakeLists.txt
  TASK1.md
  TASK2.md
  TASK3.md
  TASK4.md
  app/
    main.cc
  src/
    pricing.h
    pricing.cc

evaluator/005.pricing-ocp/
  data/
    ...
  pipeline.json
  tests/
    test_pricing.cc
```

Task progression for this case:
- `TASK1.md`: implement `m1`
- `TASK2.md`: extend to `m2`
- `TASK3.md`: extend to `m3`
- `TASK4.md`: extend to `m4`

Intent:
- `cases/005.pricing-ocp/src/` contains the pricing engine implementation.
- `cases/005.pricing-ocp/app/main.cc` contains the CLI entrypoint.
- `evaluator/005.pricing-ocp/` contains unit tests and structural checks.

---

## 1. Input

File: `order.json`

```json
{
  "subtotal": 100.0,
  "is_member": true,
  "items": 12,
  "coupons": ["SAVE10P"]
}
```

Field constraints:
- `subtotal`: number, finite, `subtotal >= 0`.
- `is_member`: boolean.
- `items`: integer, `items >= 0`.
- `coupons`: array of strings. Unknown coupon codes are allowed (they simply do not match any rule).
- Duplicate coupon codes are allowed in input but treated as a **set** for matching (i.e., duplicates do not increase effect).

Invalid input MUST cause non-zero exit code. See §7.

---

## 2. Output

File: `result.json`

```json
{
  "final_price": 70.0,
  "applied_rules": ["COUPON_SAVE10P", "ITEMS_20OFF"]
}
```

Output constraints:
- `final_price`: number, finite, rounded to **2 decimals** (nearest cent), and `final_price >= 0`.
- `applied_rules`: list of **selected** rule IDs (after group exclusivity and member-disable logic).
  - Order MUST be deterministic (see §6.3).

---

## 3. Discount Model

Each rule contributes either:
- **percent discount**: `percent` in `[0.0, 1.0]` (e.g., 0.10 means 10% off), or
- **flat discount**: `flat` in USD (e.g., 20.00 means $20 off)

### 3.1 Aggregation (applies to all milestones)

Given:
- subtotal `S`
- selected percent discounts `p1..pk`
- selected flat discounts `f1..fm`

Compute:
1) `P = clamp(sum(pi), 0.0, 0.95)`
2) `price1 = S * (1 - P)`
3) `F = sum(fi)`
4) `price2 = price1 - F`
5) `final_price = round_to_cents(max(0, price2))`

Rounding:
- Only round once at the end: `final_price = round(price2, 2)`.
- Internally use double; comparisons in harness should allow 1 cent tolerance.

---

## 4. Milestones

Milestone is provided by CLI flag `--milestone`.

### m1: Built-in rules
All matching built-in rules apply.

Rules:
- `ITEMS_20OFF` (flat=20.00): applies if `items >= 10`.
- `MEMBER_10P` (percent=0.10): applies if `is_member == true`.

### m2: Coupons (simple)
m2 includes all m1 rules, plus coupon rules. All matching rules apply.

Coupon rules:
- `COUPON_SAVE5` (flat=5.00): applies if coupon set contains `"SAVE5"`.
- `COUPON_SAVE10P` (percent=0.10): applies if coupon set contains `"SAVE10P"`.

### m3: Coupon exclusivity + member disable
m3 includes m2 rules, plus **selection constraints**:

#### (C1) Group exclusivity
Rules may belong to a group. In each group, keep **only one** rule:
- Choose the rule with highest `priority`.
- Tie-breaker: lexicographically largest `id` wins (deterministic).

Built-in m1 rules have no group.
Coupon rules belong to group `"COUPON"` with priorities:
- `COUPON_SAVE10P`: priority 20
- `COUPON_SAVE5`: priority 10

#### (C2) disables_member
If any **selected** rule has `disables_member == true`, then `MEMBER_10P` is NOT selected
(even if `is_member == true`).

For built-in rules in m1/m2/m3:
- `COUPON_SAVE10P`: disables_member = false
- `COUPON_SAVE5`: disables_member = false
- (Runtime rules in m4 may set this flag.)

### m4: Runtime rules
m4 includes m3 behavior and additionally loads rules at runtime.

Rules loading:
- Path is resolved in this order:
  1) `--rules <path>` if provided
  2) env var `NITR_RULES` if set
  3) `rules.json` in current working directory if exists
  If none found, proceed with built-in rules only.

`rules.json` schema:
```json
{
  "rules": [
    {
      "id": "BLACKFRIDAY_30P",
      "type": "percent",            // "percent" or "flat"
      "value": 0.30,                // percent in [0,1] or flat amount >= 0
      "priority": 100,              // integer (can be negative)
      "group": "COUPON",            // optional string
      "disables_member": true,      // optional bool, default false
      "when": {                     // all specified conditions must match
        "coupon": "BLACKFRIDAY",    // optional string
        "is_member": true,          // optional bool
        "min_items": 5              // optional int >= 0
      }
    }
  ]
}
```

Runtime rule semantics:
- A runtime rule matches if **all** present conditions in `when` match:
  - `coupon`: coupon set contains that string
  - `is_member`: equals input `is_member`
  - `min_items`: input `items >= min_items`
- Runtime rules participate in the same selection constraints as m3:
  - group exclusivity by priority/tie-break
  - disables_member can disable `MEMBER_10P`

Invalid runtime rules:
- If `rules.json` exists but is invalid JSON or violates schema constraints (e.g., unknown type, negative flat, percent out of range, missing id), treat as error and exit non-zero (see §7).

---

## 5. CLI Contract

Executable: `pricing`

```
pricing --in <order.json> --out <result.json> --milestone <m1|m2|m3|m4> [--rules <rules.json>]
```

- Writes `result.json` on success.
- Returns non-zero on invalid input, invalid rules file, or unsupported milestone.

---

## 6. Determinism Requirements

### 6.1 Coupon set
Treat `coupons` as a set for matching (duplicates ignored).

### 6.2 Rule selection in a group
- Highest priority wins
- Tie-break: lexicographically largest `id`

### 6.3 applied_rules order
`applied_rules` MUST be sorted by:
1) group name (empty group first), then
2) descending priority (rules without priority use 0), then
3) lexicographically ascending id

This ensures stable output for evaluation.

---

## 7. Error Handling

On error, exit code != 0 and print ONE line to stderr:

- `ERR_INVALID_JSON`
- `ERR_INVALID_SCHEMA`
- `ERR_UNSUPPORTED_MILESTONE`
- `ERR_IO`

No output file is required on failure.

---

## 8. Examples (non-normative)

Example:
Input: subtotal=100, is_member=true, items=12, coupons=["SAVE10P"]
m2: percent=0.10(member)+0.10(coupon)=0.20, flat=20 => final=100*(0.8)-20=60.00
m3: coupon group keeps SAVE10P, member still applies => same as m2
