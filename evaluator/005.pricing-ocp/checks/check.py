#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

from evaluator.shared.path_checks import (
    find_missing_paths,
    read_text,
)
from evaluator.shared.source_analysis import has_any_pattern, strip_comments_and_strings
from evaluator.shared.check_output import emit_check_result


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
    if has_any_pattern([coupon_kw], cleaned, flags=re.IGNORECASE):
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
    if find_missing_paths([case_dir]):
        return emit_check_result(
            passed=False, findings=[f"case_dir not found: {case_dir}"]
        )

    findings: list[str] = []
    for rel in args.core_files:
        p = case_dir / rel
        if find_missing_paths([p]):
            findings.append(
                f"core file missing (treated as failure): {p}"
            )
            continue

        code = read_text(p)
        vios = find_violations(code)
        if vios:
            findings.append(f"coupon dispatch branching found in {p}")
            for rule_id, snippet in vios[:20]:
                findings.append(f"{rule_id}: {snippet}")

    return emit_check_result(passed=not findings, findings=findings)


if __name__ == "__main__":
    raise SystemExit(main())
