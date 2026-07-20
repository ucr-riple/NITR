#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

CONSUMER_NAME_HINTS = ("preview", "writer", "render", "output")
TRACKER_STATE_NAMES = {"completed_totes", "current_tote"}
PACKET_ASSEMBLY_NAMES = {
    "HandoverPacket",
    "HandoverPacketRow",
    "HandoverPacketSummary",
}


@dataclass
class FunctionSignals:
    name: str
    tracker_state: set[str]
    packet_types: set[str]
    summary_signals: set[str]


def is_consumer_path(path: Path) -> bool:
    lowered = path.name.lower()
    return path.parts[0] == "app" or any(
        hint in lowered for hint in CONSUMER_NAME_HINTS
    )


def function_signals(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> FunctionSignals:
    tracker_state: set[str] = set()
    packet_types: set[str] = set()
    summary_signals: set[str] = set()

    for child in ast.walk(node):
        name: str | None = None
        if isinstance(child, ast.Name):
            name = child.id
        elif isinstance(child, ast.Attribute):
            name = child.attr
        elif isinstance(child, ast.arg):
            name = child.arg
        if name is None:
            continue

        normalized = name.strip("_")
        if normalized in TRACKER_STATE_NAMES:
            tracker_state.add(normalized)
        if normalized in PACKET_ASSEMBLY_NAMES:
            packet_types.add(normalized)
        if normalized in {
            "row_number",
            "summary",
            "total_packages",
            "tote_count",
        }:
            summary_signals.add(normalized)

    return FunctionSignals(node.name, tracker_state, packet_types, summary_signals)


def module_functions(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node)
    return functions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    required_paths = [
        case_root / "src" / "handover_packet_preview.py",
        case_root / "src" / "handover_packet_writer.py",
        case_root / "src" / "handover_packet.py",
        case_root / "src" / "shift_tracker.py",
    ]
    findings: list[str] = []

    for path in required_paths:
        if not path.is_file():
            findings.append(f"missing required path: {path.relative_to(case_root)}")
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    trees: dict[Path, ast.Module] = {}
    try:
        paths = sorted((case_root / "src").rglob("*.py"))
        app_path = case_root / "app" / "main.py"
        if app_path.is_file():
            paths.append(app_path)
        for path in paths:
            trees[path.relative_to(case_root)] = ast.parse(
                path.read_text(encoding="utf-8"), filename=str(path)
            )
    except (OSError, SyntaxError) as exc:
        print(f"FAIL: could not analyze source files: {exc}")
        return 1

    domain_producers: list[str] = []
    for path, tree in trees.items():
        for function in module_functions(tree):
            signals = function_signals(function)
            assembles_packet = bool(signals.tracker_state) and bool(
                signals.packet_types
            )

            if is_consumer_path(path):
                if signals.tracker_state and (
                    signals.packet_types or signals.summary_signals
                ):
                    findings.append(
                        f"{path}: consumer function '{signals.name}' inspects "
                        "tracker state while assembling packet content"
                    )
            elif assembles_packet:
                domain_producers.append(f"{path}:{signals.name}")

    if not domain_producers:
        findings.append(
            "no domain-side function appears to own packet assembly from tracker state"
        )

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: packet assembly remains domain-owned and consumer flows stay thin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
