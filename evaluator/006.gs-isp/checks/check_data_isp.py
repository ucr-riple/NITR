#!/usr/bin/env python3
from __future__ import annotations

"""Validate data-ISP interface extraction constraints for case 006.

Rule:
  - Require required domain headers to exist.
  - Forbid direct legacy `hit_buffer.h` usage from sort/shade/composite components.
  - Ensure each ISP family (`sort`, `shade`, `composite`) still exposes expected
    dedicated view/interface token(s).

Inputs:
  - `--case_root` (defaults to script's case root).
  - Source files:
    - `src/sort_hits.h`
    - `src/eval_shading.h`
    - `src/composite.h`
    - corresponding `.cc` files for direct include scan.

Output:
  - emit_check_result(passed=<bool>, findings=[violation messages]).
"""

import argparse
from pathlib import Path

from evaluator.shared.path_checks import (
    case_root_from_script,
    find_missing_paths,
    read_text,
)
from evaluator.shared.source_analysis import has_any_substring
from evaluator.shared.check_output import emit_check_result

REQUIRED_HEADERS = [
    "sort_hits.h",
    "eval_shading.h",
    "composite.h",
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

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()

    src_dir = case_root / "src"

    findings: list[str] = []
    required_headers = [src_dir / header for header in REQUIRED_HEADERS]
    for header in find_missing_paths(required_headers):
        findings.append(f"Missing required header: {header}")

    sort_text = read_text(src_dir / "sort_hits.h", missing_ok=False)
    shade_text = read_text(src_dir / "eval_shading.h", missing_ok=False)
    comp_text = read_text(src_dir / "composite.h", missing_ok=False)

    for token in FORBIDDEN_IN_SORT_HEADER:
        if token in sort_text:
            findings.append("sort_hits.h still exposes legacy HitBuffer/Hit types.")
            break

    for path in [
        src_dir / "sort_hits.h",
        src_dir / "eval_shading.h",
        src_dir / "composite.h",
        src_dir / "sort_hits.cc",
        src_dir / "eval_shading.cc",
        src_dir / "composite.cc",
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
