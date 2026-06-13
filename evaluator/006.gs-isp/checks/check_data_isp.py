#!/usr/bin/env python3
from __future__ import annotations

from evaluator.shared.check_utils import (
    case_root_from_script,
    die_message,
    find_missing_paths,
    has_any_substring,
    read_text,
)

ROOT = case_root_from_script(__file__)
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

def main() -> int:
    for header in find_missing_paths(REQUIRED_HEADERS):
        die_message(f"Missing required header: {header}")

    sort_text = read_text(SRC / "sort_hits.h", missing_ok=False)
    shade_text = read_text(SRC / "eval_shading.h", missing_ok=False)
    comp_text = read_text(SRC / "composite.h", missing_ok=False)

    for token in FORBIDDEN_IN_SORT_HEADER:
        if token in sort_text:
            die_message("sort_hits.h still exposes legacy HitBuffer/Hit types.")

    for path in [
        SRC / "sort_hits.h",
        SRC / "eval_shading.h",
        SRC / "composite.h",
        SRC / "sort_hits.cc",
        SRC / "eval_shading.cc",
        SRC / "composite.cc",
    ]:
        text = read_text(path, missing_ok=False)
        if FORBIDDEN_INCLUDE in text:
            die_message(f"{path.name} still includes hit_buffer.h directly.")

    joined = sort_text + shade_text + comp_text
    for group_name, tokens in VIEW_TOKEN_FAMILIES.items():
        if not has_any_substring(tokens, joined):
            die_message(
                f"Expected {group_name} interface/view token not found: one of {tokens}"
            )

    print("Structural ISP checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
