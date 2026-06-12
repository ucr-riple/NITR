#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluator.shared.check_utils import read_text, strip_comments_and_strings


def find_violations(code: str) -> list[tuple[str, str]]:
    """
    Return list of (rule_id, matched_snippet) violations.
    Rule: no if/else-if/switch branching on coupon/coupon_code/couponType/etc.
    """
    violations = []
    cleaned = strip_comments_and_strings(code)

    # Heuristics: "coupon" family keywords (customize if your struct names differ)
    coupon_kw = r"(coupon|coupon_code|couponCode|coupon_type|couponType|promo|promo_code|promoCode)"

    # 1) if (...) that references coupon keywords
    if_pat = re.compile(rf"\bif\s*\(([^)]*{coupon_kw}[^)]*)\)", re.IGNORECASE)
    for m in if_pat.finditer(cleaned):
        snippet = m.group(0)[:200]
        violations.append(("NO_IF_ON_COUPON", snippet))

    # 2) else if (...) that references coupon keywords
    elif_pat = re.compile(rf"\belse\s+if\s*\(([^)]*{coupon_kw}[^)]*)\)", re.IGNORECASE)
    for m in elif_pat.finditer(cleaned):
        snippet = m.group(0)[:200]
        violations.append(("NO_ELSEIF_ON_COUPON", snippet))

    # 3) switch (...) that references coupon keywords
    sw_pat = re.compile(rf"\bswitch\s*\(([^)]*{coupon_kw}[^)]*)\)", re.IGNORECASE)
    for m in sw_pat.finditer(cleaned):
        snippet = m.group(0)[:200]
        violations.append(("NO_SWITCH_ON_COUPON", snippet))

    # 4) case labels that look like coupon codes (optional, strict)
    # If you use enums like CouponType::VIP, this will catch the "case" lines.
    # Comment out if too strict.
    case_pat = re.compile(r"\bcase\s+[^:]+:", re.IGNORECASE)
    # Only flag cases if the file has a coupon-related switch/if somewhere.
    if re.search(coupon_kw, cleaned, flags=re.IGNORECASE):
        for m in case_pat.finditer(cleaned):
            snippet = m.group(0)[:200]
            violations.append(("NO_CASE_DISPATCH_IN_COUPON_CONTEXT", snippet))

    return violations


def main() -> int:
    """Reject coupon-dispatch branching in the configured core files."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--case_dir", required=True, help="e.g. cases/pricing-ocp")
    ap.add_argument(
        "--core_files",
        nargs="+",
        default=["src/pricing.cc"],
        help="Files (relative to case_dir) to enforce OCP coupon dispatch ban.",
    )
    args = ap.parse_args()

    case_dir = Path(args.case_dir)
    if not case_dir.exists():
        print(f"[gate2] case_dir not found: {case_dir}", file=sys.stderr)
        return 2

    any_violation = False
    for rel in args.core_files:
        p = case_dir / rel
        if not p.exists():
            print(
                f"[gate2] core file missing (treated as failure): {p}", file=sys.stderr
            )
            any_violation = True
            continue

        code = read_text(p)
        vios = find_violations(code)
        if vios:
            any_violation = True
            print(
                f"[gate2] FAIL: coupon dispatch branching found in {p}", file=sys.stderr
            )
            for rule_id, snippet in vios[:20]:
                print(f"  - {rule_id}: {snippet}", file=sys.stderr)

    if any_violation:
        print("[gate2] OCP check failed.", file=sys.stderr)
        return 1

    print("[gate2] PASS: no coupon dispatch branching in core files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
