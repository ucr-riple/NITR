#!/usr/bin/env python3

"""Enforce remaining explainability-boundary constraints for case 019.

Rule:
  - Ranker core should stay free from display-oriented string literals.
  - `RankedItem` should remain present and compact instead of absorbing many fields.

Inputs:
  - `--case_root` (defaults to script-inferred case root)
  - Source files under `src/`:
      - `ranker.cc`, `ranker.h`
      - `ranking_result.h`
      - `item.h`

Output:
  - `{"passed": bool, "findings": [violations]}` via emit_check_result.
"""

import argparse
from pathlib import Path
import re
from typing import List

from evaluator.shared.module.path_checks import case_root_from_script, read_text
from evaluator.shared.module.source_analysis import strip_comments
from evaluator.shared.check_output import emit_check_result


def remove_include_lines(text: str) -> str:
    """Drop include directives before scanning for display-oriented tokens."""
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#include")
    )


def string_literals(text: str) -> List[str]:
    """Extract string literals that may indicate leaked presentation concerns."""
    return re.findall(r'"(?:\\.|[^"\\])*"', text)


def struct_body(text: str, struct_name: str) -> str:
    """Return the body of a named struct for lightweight field counting."""
    match = re.search(rf"struct\s+{struct_name}\s*\{{(.*?)\}};", text, flags=re.S)
    if not match:
        return ""
    return match.group(1)


def count_field_lines(body: str) -> int:
    """Count likely field declarations in a struct body."""
    count = 0
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("//"):
            continue
        if line.endswith(";"):
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root", type=Path, default=case_root_from_script(__file__)
    )
    args = parser.parse_args()

    root = args.case_root.resolve()
    src = root / "src"
    failures: List[str] = []

    ranker_text = strip_comments(
        remove_include_lines(
            read_text(src / "ranker.cc") + "\n" + read_text(src / "ranker.h")
        )
    )
    ranker_literals = string_literals(ranker_text)
    if ranker_literals:
        failures.append(
            "ranker core should not contain display-oriented string literals"
        )

    ranking_result_text = strip_comments(read_text(src / "ranking_result.h"))
    ranked_body = struct_body(ranking_result_text, "RankedItem")
    if not ranked_body:
        failures.append("ranking_result.h must define RankedItem")
    else:
        field_count = count_field_lines(ranked_body)
        if field_count > 3:
            failures.append(
                "RankedItem should stay compact and not accumulate many fields"
            )

    return emit_check_result(passed=not failures, findings=failures)


if __name__ == "__main__":
    raise SystemExit(main())
