#!/usr/bin/env python3
from evaluator.shared.path_checks import case_root_from_script, read_text
from evaluator.shared.source_analysis import find_matching_patterns

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
    for pat in violations:
        print(f"FAIL: forbidden pattern in map_snapshot.cc: {pat}")
    if violations:
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
