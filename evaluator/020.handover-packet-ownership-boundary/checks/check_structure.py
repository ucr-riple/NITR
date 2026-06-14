#!/usr/bin/env python3

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from evaluator.shared.path_checks import (
    case_root_from_script,
    read_text,
    scan_files,
)
from evaluator.shared.source_analysis import (
    count_matching_patterns,
    has_any_substring,
    regex_matches,
)


CONSUMER_FILES = {
    "handover_packet_preview.cc",
    "handover_packet_preview.h",
    "handover_packet_writer.cc",
    "handover_packet_writer.h",
}

DOMAIN_CORE_FILES = {
    "shift_tracker.cc",
    "shift_tracker.h",
    "handover_packet.cc",
    "handover_packet.h",
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

SUMMARY_SIGNAL_PATTERNS = [
    re.compile(r"package_count"),
    re.compile(r"tote_count"),
    re.compile(r"total_packages"),
]

TRACKER_PARAM_PATTERN = re.compile(r"ShiftTracker\s*(?:&|\*)")
PACKET_RETURN_PATTERN = re.compile(r"\bHandoverPacket\b")


@dataclass
class Finding:
    code: str
    path: str
    message: str


def has_tracker_param(text: str) -> bool:
    """Detect APIs that directly accept a ShiftTracker dependency."""
    return regex_matches(TRACKER_PARAM_PATTERN, text)


def has_packet_mentions(text: str) -> bool:
    """Detect whether a file mentions the HandoverPacket domain type."""
    return regex_matches(PACKET_RETURN_PATTERN, text)


def is_consumer_side(path: Path) -> bool:
    """Classify files that should remain on the preview/writer/app consumer side."""
    if path in CONSUMER_FILES:
        return True
    name = path.name.lower()
    return any(hint in name for hint in CONSUMER_NAME_HINTS)


def find_domain_assembly_candidates(files: list[Path], src_dir: Path, case_root: Path) -> list[str]:
    """Find likely domain-side files that own packet assembly responsibilities."""
    candidates: list[str] = []
    for path in files:
        text = read_text(path, missing_ok=False)

        if is_consumer_side(path):
            continue

        if path in {src_dir / "handover_packet.cc", src_dir / "handover_packet.h"}:
            if has_tracker_param(text) and has_packet_mentions(text):
                candidates.append(str(path.relative_to(case_root)))
            continue

        if path in {src_dir / "shift_tracker.cc", src_dir / "shift_tracker.h"}:
            if "HandoverPacket" in text:
                candidates.append(str(path.relative_to(case_root)))
            continue

        if has_tracker_param(text) and has_packet_mentions(text):
            candidates.append(str(path.relative_to(case_root)))
    return candidates


def main() -> int:
    """Report whether packet assembly logic leaked into consumer-side files."""

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

    consumer_files: list[Path] = [src_dir / consumer_file for consumer_file in CONSUMER_FILES] + [app_file]
    
    consumer_assembly_sites: list[str] = []

    domain_core_files = {src_dir / core_file for core_file in DOMAIN_CORE_FILES}

    for path in source_files:
        text = read_text(path, missing_ok=False)
        rel_path = str(path.relative_to(case_root))
        assembly_score = count_matching_patterns(ASSEMBLY_SIGNAL_PATTERNS, text)
        summary_score = count_matching_patterns(SUMMARY_SIGNAL_PATTERNS, text)
        tracker_param = has_tracker_param(text)
        packet_mentions = has_packet_mentions(text)

        if path in consumer_files:
            if assembly_score >= 2 and has_any_substring(
                ["current_tote", "completed_totes"], text
            ):
                consumer_assembly_sites.append(rel_path)
                findings.append(
                    Finding(
                        code="consumer_assembly_logic",
                        path=rel_path,
                        message="consumer-side file inspects tracker state and assembles packet rows",
                    )
                )
            if summary_score >= 2 and has_any_substring(
                ["summary", "total_packages"], text
            ):
                findings.append(
                    Finding(
                        code="consumer_summary_logic",
                        path=rel_path,
                        message="consumer-side file computes packet summary from live tracker state",
                    )
                )
            continue

        if path in domain_core_files:
            continue

        if tracker_param and packet_mentions and is_consumer_side(path):
            findings.append(
                Finding(
                    code="shared_output_side_helper",
                    path=rel_path,
                    message="consumer-side helper accepts ShiftTracker and packet types together",
                )
            )
            if assembly_score >= 2 or summary_score >= 2:
                findings.append(
                    Finding(
                        code="shared_output_side_assembly",
                        path=rel_path,
                        message="consumer-side helper appears to assemble packet content from tracker state",
                    )
                )
        elif (
            tracker_param
            and packet_mentions
            and (assembly_score >= 2 or summary_score >= 2)
        ):
            # Non-consumer helper under src can be a valid domain-side assembly module.
            pass

    if len(consumer_assembly_sites) >= 2:
        findings.append(
            Finding(
                code="duplicated_consumer_assembly",
                path=",".join(consumer_assembly_sites),
                message="more than one consumer-side file appears to assemble packet content",
            )
        )

    domain_candidates = find_domain_assembly_candidates(source_files)
    if not domain_candidates:
        findings.append(
            Finding(
                code="missing_domain_side_packet_api",
                path="src",
                message="no domain-side file appears to own packet assembly or expose a packet-producing API",
            )
        )

    passed = not findings
    summary = {
        "suite": "structural",
        "passed": passed,
        "findings": [finding.__dict__ for finding in findings],
        "domain_candidates": domain_candidates,
        "checked_files": [str(path.relative_to(case_root)) for path in source_files],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
