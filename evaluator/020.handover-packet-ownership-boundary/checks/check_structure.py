#!/usr/bin/env python3

"""Detect remaining cross-file handover-packet ownership boundary violations.

Rule:
  - More than one consumer-side file should not appear to assemble packet content.
  - Keep the remaining cross-file aggregation check that is less natural in pipeline JSON.

Inputs:
  - `--case_root` (defaults to script's case root).
  - Source files under `src/` plus `app/main.cc`.

Behavior:
  - Scores files against assembly/summary signal patterns and tracker/packet coupling.
  - Emits structured findings with file classification and code.

Output:
  - Prints a JSON summary and returns 0/1 via process exit.
"""

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from evaluator.shared.module.path_checks import (
    case_root_from_script,
    read_text,
    scan_files,
)
from evaluator.shared.module.source_analysis import (
    count_matching_patterns,
    has_any_substring,
)
from evaluator.shared.check_output import CHECK_FAILED, CHECK_PASSED


CONSUMER_FILES = {
    "handover_packet_preview.cc",
    "handover_packet_preview.h",
    "handover_packet_writer.cc",
    "handover_packet_writer.h",
}

CONSUMER_NAME_HINTS = ("preview", "writer", "render", "output", "main")

ASSEMBLY_SIGNAL_PATTERNS = [
    re.compile(r"completed_totes\s*\("),
    re.compile(r"current_tote\s*\("),
    re.compile(r"HandoverPacketRow\s*\{"),
    re.compile(r"rows\s*\.\s*push_back\s*\("),
    re.compile(r"summary\s*="),
    re.compile(r"row_number"),
]


@dataclass
class Finding:
    code: str
    path: str
    message: str


def is_consumer_side(path: Path) -> bool:
    """Classify files that should remain on the preview/writer/app consumer side."""
    if path in CONSUMER_FILES:
        return True
    name = path.name.lower()
    return any(hint in name for hint in CONSUMER_NAME_HINTS)


def main() -> int:
    """Report remaining cross-file consumer assembly duplication."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    src_dir = case_root / "src"

    app_file = case_root / "app" / "main.cc"

    findings: list[Finding] = []
    source_files = scan_files(src_dir, suffixes=(".h", ".cc")) + [app_file]

    consumer_files: list[Path] = [
        src_dir / consumer_file for consumer_file in CONSUMER_FILES
    ] + [app_file]

    consumer_assembly_sites: list[str] = []

    for path in source_files:
        text = read_text(path, missing_ok=False)
        rel_path = str(path.relative_to(case_root))
        assembly_score = count_matching_patterns(ASSEMBLY_SIGNAL_PATTERNS, text)

        if path in consumer_files:
            if assembly_score >= 2 and has_any_substring(
                ["current_tote", "completed_totes"], text
            ):
                consumer_assembly_sites.append(rel_path)
            continue

    if len(consumer_assembly_sites) >= 2:
        findings.append(
            Finding(
                code="duplicated_consumer_assembly",
                path=",".join(consumer_assembly_sites),
                message="more than one consumer-side file appears to assemble packet content",
            )
        )

    passed = not findings
    summary = {
        "suite": "structural",
        "passed": passed,
        "findings": [finding.__dict__ for finding in findings],
        "checked_files": [str(path.relative_to(case_root)) for path in source_files],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return CHECK_PASSED if passed else CHECK_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
