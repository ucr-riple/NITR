#!/usr/bin/env python3
from evaluator.shared.path_checks import case_root_from_script, read_text
from evaluator.shared.source_analysis import find_matching_patterns
from evaluator.shared.check_output import emit_check_result

ROOT = case_root_from_script(__file__)
SRC = ROOT / "src" / "map_snapshot.cc"

FORBIDDEN = [
    r"\bGeometryProvider\b",
    r"\bSemanticsProvider\b",
    r'type\s*==\s*"',
    r"CreateProviderHardcoded",
]


def main() -> int:
    """Reject provider knowledge and hardcoded type dispatch inside map_snapshot.cc."""
    txt = read_text(SRC, missing_ok=False)
    violations = find_matching_patterns(FORBIDDEN, txt)
    findings = [f"forbidden pattern in map_snapshot.cc: {pat}" for pat in violations]
    return emit_check_result(passed=not findings, findings=findings)


if __name__ == "__main__":
    raise SystemExit(main())
