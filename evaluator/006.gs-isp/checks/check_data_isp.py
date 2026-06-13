#!/usr/bin/env python3
from __future__ import annotations

from evaluator.shared.path_checks import (
    case_root_from_script,
    find_missing_paths,
    read_text,
)
from evaluator.shared.source_analysis import has_any_substring
from evaluator.shared.check_output import emit_check_result

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

    findings: list[str] = []
    for header in find_missing_paths(REQUIRED_HEADERS):
        findings.append(f"Missing required header: {header}")

    sort_text = read_text(SRC / "sort_hits.h", missing_ok=False)
    shade_text = read_text(SRC / "eval_shading.h", missing_ok=False)
    comp_text = read_text(SRC / "composite.h", missing_ok=False)

    for token in FORBIDDEN_IN_SORT_HEADER:
        if token in sort_text:
            findings.append("sort_hits.h still exposes legacy HitBuffer/Hit types.")
            break

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
            findings.append(f"{path.name} still includes hit_buffer.h directly.")

    joined = sort_text + shade_text + comp_text
    for group_name, tokens in VIEW_TOKEN_FAMILIES.items():
        if not has_any_substring(tokens, joined):
            findings.append(
                f"Expected {group_name} interface/view token not found: one of {tokens}"
            )

    return emit_check_result(passed=not findings, findings=findings)


if __name__ == "__main__":
    raise SystemExit(main())
