#!/usr/bin/env python3

"""Enforce DIP-like structural constraints for case 008.

Rule:
  - Reject hardcoded geometry/semantics provider references and type-string dispatch
    inside `src/map_snapshot.cc`.

Inputs:
  - `--case_root` (defaults to script-inferred case root).

Inputs checked:
  - `src/map_snapshot.cc`

Output:
  - emit_check_result(passed=<bool>, findings=[pattern-based violations]).
"""

import argparse
from pathlib import Path

from evaluator.shared.module.path_checks import case_root_from_script, read_text
from evaluator.shared.module.source_analysis import find_matching_patterns
from evaluator.shared.check_output import emit_check_result

FORBIDDEN = [
    r"\bGeometryProvider\b",
    r"\bSemanticsProvider\b",
    r'type\s*==\s*"',
    r"CreateProviderHardcoded",
]


def main() -> int:
    """Reject provider knowledge and hardcoded type dispatch inside map_snapshot.cc."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    src = case_root / "src" / "map_snapshot.cc"
    txt = read_text(src, missing_ok=False)
    violations = find_matching_patterns(FORBIDDEN, txt)

    findings = [f"forbidden pattern in map_snapshot.cc: {pat}" for pat in violations]

    return emit_check_result(passed=not findings, findings=findings)


if __name__ == "__main__":
    raise SystemExit(main())
