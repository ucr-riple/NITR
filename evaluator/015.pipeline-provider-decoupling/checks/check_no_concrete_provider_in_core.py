#!/usr/bin/env python3

"""Disallow concrete provider dependencies in pipeline runner core files.

Rule:
  - `pipeline_runner.h` and `pipeline_runner.cc` must not reference concrete
    provider headers or concrete provider class names.

Inputs:
  - `--case_root` (defaults to script's case root).
  - Source files:
    - `src/pipeline_runner.h`
    - `src/pipeline_runner.cc`

Output:
  - emit_check_result(passed=<bool>, findings=[one or more violation strings]).
"""

import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
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
