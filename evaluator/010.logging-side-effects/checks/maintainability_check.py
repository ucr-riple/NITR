import re

from evaluator.shared.path_checks import (
    case_root_from_script,
    read_text,
)
from evaluator.shared.source_analysis import (
    find_matching_substrings,
    has_any_pattern,
    has_any_substring,
)

ROOT = case_root_from_script(__file__)
SRC = ROOT / "src"

def main() -> int:
    policy_h = read_text(SRC / "loan_policy.h", missing_ok=False)
    policy_cc = read_text(SRC / "loan_policy.cc", missing_ok=False)
    service_cc = read_text(SRC / "loan_review_service.cc", missing_ok=False)
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

    if errors:
        for error in errors:
            print(error)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
