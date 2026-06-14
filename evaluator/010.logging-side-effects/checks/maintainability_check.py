#!/usr/bin/env python3

"""Enforce logging-side-effects constraints for case 010.

Rules:
  - `loan_policy.{h,cc}` must not depend on logging infrastructure headers (`audit_logger.h`).
  - `loan_policy.h` must expose `EvaluateApplicant` with a dependency-safe signature
    (no logger/audit dependency parameters).
  - `loan_policy.cc` must avoid direct I/O and direct audit emission.
  - `loan_review_service.cc` should be the place where audit emission is localized.

Inputs:
  - `--case_root` (defaults to script-inferred case root)
  - Files:
      - `src/loan_policy.h`
      - `src/loan_policy.cc`
      - `src/loan_review_service.cc`

Output:
  - `{"passed": bool, "findings": [rule violation strings]}` via emit_check_result.
"""

import argparse
from pathlib import Path
import re

from evaluator.shared.path_checks import (
    case_root_from_script,
    read_text,
)
from evaluator.shared.check_output import emit_check_result
from evaluator.shared.source_analysis import (
    find_matching_substrings,
    has_any_pattern,
    has_any_substring,
)


def main() -> int:

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()
    case_root = args.case_root.resolve()
    src = case_root / "src"

    policy_h = read_text(src / "loan_policy.h", missing_ok=False)
    policy_cc = read_text(src / "loan_policy.cc", missing_ok=False)
    service_cc = read_text(src / "loan_review_service.cc", missing_ok=False)
    errors = []

    policy_all = policy_h + "\n" + policy_cc
    if has_any_substring(["audit_logger.h"], policy_all):
        errors.append("loan_policy must not depend on audit_logger.h")

    signature_patterns = [
        r"ReviewDecision\s+EvaluateApplicant\s*\(([^)]*)\)",
    ]
    if not has_any_pattern(signature_patterns, policy_h):
        errors.append("Could not find EvaluateApplicant signature in loan_policy.h")
    else:
        signature_match = re.search(signature_patterns[0], policy_h)
        signature = signature_match.group(1)
        lowered = signature.lower()
        if "logger" in lowered or "audit" in lowered:
            errors.append(
                "EvaluateApplicant must not accept a logger or audit dependency"
            )

    direct_io_tokens = [
        "std::cout",
        "std::cerr",
        "printf(",
        "fprintf(",
        "ofstream",
        "fstream",
    ]
    for banned in find_matching_substrings(direct_io_tokens, policy_cc):
        errors.append(f"loan_policy.cc must not perform direct IO: found {banned}")

    if has_any_substring([".Log(", "->Log("], policy_cc):
        errors.append("loan_policy.cc must not emit audit logs directly")

    if not has_any_substring([".Log(", "->Log("], service_cc):
        errors.append("loan_review_service.cc should localize audit emission")

    return emit_check_result(passed=not errors, findings=errors)


if __name__ == "__main__":
    raise SystemExit(main())
