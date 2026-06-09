#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = (
    Path(__file__).resolve().parents[3]
    / "cases"
    / Path(__file__).resolve().parents[1].name
)
SRC = ROOT / "src" / "map_snapshot.cc"


def main():
    """Reject provider knowledge and hardcoded type dispatch inside map_snapshot.cc."""
    txt = SRC.read_text()
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
