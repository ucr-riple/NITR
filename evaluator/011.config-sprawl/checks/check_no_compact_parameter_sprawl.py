#!/usr/bin/env python3

"""Detect compact-mode leakage into the report renderer API for case 011.

Rule:
  - Flag function signatures that still expose a `compact_mode` parameter in
    report rendering APIs, because this case expects compact-mode behavior to be
    removed from core renderer signatures.

Inputs:
  - `--case_root` (defaults to script-location case directory).

Inputs checked:
  - cases/011.config-sprawl/src/report_renderer.h
  - cases/011.config-sprawl/src/report_renderer.cc

Output:
  - Uses emit_check_result(passed=<bool>, findings=<list[str]>)
    with one finding per matching signature.
"""

import argparse
import re
from pathlib import Path

from evaluator.shared.module.path_checks import case_root_from_script, read_text
from evaluator.shared.check_output import emit_check_result

SIGNATURE_RE = re.compile(r"^[^\n;{}]*\([^\n)]*\bcompact_mode\b[^\n)]*\)")


def main() -> int:

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()
    case_root = args.case_root.resolve()
    source_files = [
        case_root / "src" / "report_renderer.h",
        case_root / "src" / "report_renderer.cc",
    ]

    violations = []
    for path in source_files:
        text = read_text(path, missing_ok=False)
        for match in SIGNATURE_RE.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            violations.append(
                f"{path.relative_to(case_root)}:{line_no}: standalone compact_mode parameter in function signature"
            )

    return emit_check_result(passed=not violations, findings=violations)


if __name__ == "__main__":
    raise SystemExit(main())
