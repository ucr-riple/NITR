#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parents[1]
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.filter_parser import parse_inline_filter


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: main.py '<field><op><value>'")
        return 1

    result = parse_inline_filter(argv[1])
    if not result.ok:
        print(result.error.message)
        return 2

    print(result.rule)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
