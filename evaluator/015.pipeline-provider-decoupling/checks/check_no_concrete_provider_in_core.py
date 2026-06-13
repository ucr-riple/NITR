#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from evaluator.shared.path_checks import case_root_from_script, read_text
from evaluator.shared.check_output import emit_check_result

FORBIDDEN = [
    "static_policy_provider.h",
    "file_policy_provider.h",
    "StaticPolicyProvider",
    "FilePolicyProvider",
]


def main() -> int:
    """Reject concrete provider references from the pipeline runner core surface."""
    case_root = case_root_from_script(__file__)
    violations = []
    for path in [
        case_root / "src/pipeline_runner.h",
        case_root / "src/pipeline_runner.cc",
    ]:
        text = read_text(path, missing_ok=False)
        for token in FORBIDDEN:
            if token in text:
                violations.append(
                    f"Forbidden concrete provider dependency in {path}: {token}"
                )
    return emit_check_result(passed=not violations, findings=violations)


if __name__ == "__main__":
    raise SystemExit(main())
