#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import re
import sys

ROOT = (
    pathlib.Path(__file__).resolve().parents[3]
    / "cases"
    / pathlib.Path(__file__).resolve().parents[1].name
)
SRC = ROOT / "src"

REQUIRED_HEADERS = [
    SRC / "sort_hits.h",
    SRC / "eval_shading.h",
    SRC / "composite.h",
]

FORBIDDEN_INCLUDE = '#include "hit_buffer.h"'
FORBIDDEN_IN_SORT_HEADER = ["HitBuffer", "Hit "]
VIEW_TOKEN_FAMILIES = {
    "sort": [
        "SortView",
        "SortHitView",
        "SortableHitView",
        "MutableHitView",
        "HitSortView",
        "IHitSorting",
    ],
    "shade": [
        "ShadeView",
        "ShadingView",
        "ShadeHitView",
        "ShadingHitView",
        "MutableHitView",
        "IHitShading",
    ],
    "composite": [
        "CompositeView",
        "CompositeHitView",
        "CompositingView",
        "ReadonlyHitView",
        "ConstHitView",
        "IHitComposite",
    ],
}


def fail(message: str) -> None:
    """Print a structural failure message and terminate immediately."""
    print(message)
    sys.exit(1)


for header in REQUIRED_HEADERS:
    if not header.exists():
        fail(f"Missing required header: {header}")

sort_text = (SRC / "sort_hits.h").read_text()
shade_text = (SRC / "eval_shading.h").read_text()
comp_text = (SRC / "composite.h").read_text()

for token in FORBIDDEN_IN_SORT_HEADER:
    if token in sort_text:
        fail("sort_hits.h still exposes legacy HitBuffer/Hit types.")

for path in [
    SRC / "sort_hits.h",
    SRC / "eval_shading.h",
    SRC / "composite.h",
    SRC / "sort_hits.cc",
    SRC / "eval_shading.cc",
    SRC / "composite.cc",
]:
    text = path.read_text()
    if FORBIDDEN_INCLUDE in text:
        fail(f"{path.name} still includes hit_buffer.h directly.")

joined = sort_text + shade_text + comp_text
for group_name, tokens in VIEW_TOKEN_FAMILIES.items():
    if not any(token in joined for token in tokens):
        fail(f"Expected {group_name} interface/view token not found: one of {tokens}")

print("Structural ISP checks passed.")
