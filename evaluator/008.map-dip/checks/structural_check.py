#!/usr/bin/env python3
import re
from pathlib import Path

import sys

from evaluator.shared.check_utils import case_root_from_script, read_text

ROOT = case_root_from_script(__file__)
SRC = ROOT / "src" / "map_snapshot.cc"


def main() -> int:
    """Reject provider knowledge and hardcoded type dispatch inside map_snapshot.cc."""
    txt = read_text(SRC, missing_ok=False)
    forbidden = [
        r"\bGeometryProvider\b",
        r"\bSemanticsProvider\b",
        r'type\s*==\s*"',
        r"CreateProviderHardcoded",
    ]
    for pat in forbidden:
        if re.search(pat, txt):
            print(f"FAIL: forbidden pattern in map_snapshot.cc: {pat}")
            return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
