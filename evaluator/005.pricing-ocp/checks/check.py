#!/usr/bin/env python3

"""Detect control-flow dispatch patterns that violate OCP style in pricing case.

Rule:
  - Reject branch-based coupon dispatching (`if/else-if/switch/case`) in the
    configured core files.

Inputs:
  - `--case_root` (defaults to script-inferred case directory).
  - `--core_files` (default: `src/pricing.cc`).

Behavior:
  - Strips comments/strings, scans for coupon-like keywords, and reports the first
    matching snippets for visibility.

Output:
  - emit_check_result(passed=<bool>, findings=[rule/snippet messages]).
"""

import argparse
import re
from pathlib import Path

from evaluator.shared.path_checks import (
    case_root_from_script,
    find_missing_paths,
    read_text,
)
from evaluator.shared.source_analysis import (
    find_pattern_snippets,
    has_any_pattern,
    strip_comments_and_strings,
)
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
    if_pat = rf"\bif\s*\(([^)]*{coupon_kw}[^)]*)\)"
    for snippet in find_pattern_snippets(
        if_pat, cleaned, flags=re.IGNORECASE, max_chars=200
    ):
        violations.append(("NO_IF_ON_COUPON", snippet))

    # 2) else if (...) that references coupon keywords
    elif_pat = rf"\belse\s+if\s*\(([^)]*{coupon_kw}[^)]*)\)"
    for snippet in find_pattern_snippets(
        elif_pat, cleaned, flags=re.IGNORECASE, max_chars=200
    ):
        violations.append(("NO_ELSEIF_ON_COUPON", snippet))

    # 3) switch (...) that references coupon keywords
    sw_pat = rf"\bswitch\s*\(([^)]*{coupon_kw}[^)]*)\)"
    for snippet in find_pattern_snippets(
        sw_pat, cleaned, flags=re.IGNORECASE, max_chars=200
    ):
        violations.append(("NO_SWITCH_ON_COUPON", snippet))

    # 4) case labels that look like coupon codes (optional, strict)
    # If you use enums like CouponType::VIP, this will catch the "case" lines.
    # Comment out if too strict.
    case_pat = r"\bcase\s+[^:]+:"
    # Only flag cases if the file has a coupon-related switch/if somewhere.
    if has_any_pattern([coupon_kw], cleaned, flags=re.IGNORECASE):
        for snippet in find_pattern_snippets(
            case_pat, cleaned, flags=re.IGNORECASE, max_chars=200
        ):
            violations.append(("NO_CASE_DISPATCH_IN_COUPON_CONTEXT", snippet))

    return violations


def main() -> int:
    """Reject coupon-dispatch branching in the configured core files."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
        help="Path to the case root (defaults to the case inferred from this script).",
    )
    ap.add_argument(
        "--core_files",
        nargs="+",
        default=["src/pricing.cc"],
        help="Files (relative to case_root) to enforce OCP coupon dispatch ban.",
    )
    args = ap.parse_args()

    case_root = args.case_root.resolve()
    if find_missing_paths([case_root]):
        return emit_check_result(
            passed=False, findings=[f"case_root not found: {case_root}"]
        )

    findings: list[str] = []
    for rel in args.core_files:
        p = case_root / rel
        if find_missing_paths([p]):
            findings.append(f"core file missing (treated as failure): {p}")
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
