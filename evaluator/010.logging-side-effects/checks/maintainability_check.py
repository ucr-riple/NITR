from pathlib import Path
import re
import sys

from evaluator.shared.check_utils import case_root_from_script, read_text

ROOT = case_root_from_script(__file__)
SRC = ROOT / "src"

def main() -> int:
    policy_h = read_text(SRC / "loan_policy.h", missing_ok=False)
    policy_cc = read_text(SRC / "loan_policy.cc", missing_ok=False)
    service_cc = read_text(SRC / "loan_review_service.cc", missing_ok=False)
    errors = []

    policy_all = policy_h + "\n" + policy_cc
    if "audit_logger.h" in policy_all:
        errors.append("loan_policy must not depend on audit_logger.h")

    signature_match = re.search(
        r"ReviewDecision\s+EvaluateApplicant\s*\(([^)]*)\)", policy_h
    )
    if not signature_match:
        errors.append("Could not find EvaluateApplicant signature in loan_policy.h")
    else:
        signature = signature_match.group(1)
        lowered = signature.lower()
        if "logger" in lowered or "audit" in lowered:
            errors.append(
                "EvaluateApplicant must not accept a logger or audit dependency"
            )

    for banned in [
        "std::cout",
        "std::cerr",
        "printf(",
        "fprintf(",
        "ofstream",
        "fstream",
    ]:
        if banned in policy_cc:
            errors.append(f"loan_policy.cc must not perform direct IO: found {banned}")

    if ".Log(" in policy_cc or "->Log(" in policy_cc:
        errors.append("loan_policy.cc must not emit audit logs directly")

    if ".Log(" not in service_cc and "->Log(" not in service_cc:
        errors.append("loan_review_service.cc should localize audit emission")

    if errors:
        for error in errors:
            print(error)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
