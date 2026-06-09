#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CASE_NAME = Path(__file__).resolve().parents[1].name
ROOT = REPO_ROOT / "cases" / CASE_NAME
EVALUATOR_ROOT = REPO_ROOT / "evaluator" / CASE_NAME
HARNESS = EVALUATOR_ROOT / "tests" / "functional_harness.cc"
SRC_DIR = ROOT / "src"
DATA_DIR = EVALUATOR_ROOT / "data"


def compile_harness(binary_path: Path) -> None:
    """Compile the functional harness against the case sources under test."""
    cmd = [
        "c++",
        "-std=c++17",
        "-I",
        str(SRC_DIR),
        str(HARNESS),
        str(SRC_DIR / "handover_packet.cc"),
        str(SRC_DIR / "handover_packet_preview.cc"),
        str(SRC_DIR / "handover_packet_writer.cc"),
        str(SRC_DIR / "shift_tracker.cc"),
        "-o",
        str(binary_path),
    ]
    subprocess.run(cmd, check=True, cwd=ROOT)


def run_case(binary_path: Path, scenario: str, *output_paths: Path) -> dict:
    """Run one harness scenario and parse its JSON result payload."""
    cmd = [str(binary_path), scenario, *[str(path) for path in output_paths]]
    completed = subprocess.run(
        cmd,
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def expect_equal(name: str, actual: str, expected: str, failures: list[str]) -> None:
    """Record a named failure when two expected values differ."""
    if actual != expected:
        failures.append(f"{name} mismatch")


def expect_true(name: str, condition: bool, failures: list[str]) -> None:
    """Record a named failure when a required condition is false."""
    if not condition:
        failures.append(name)


def main() -> int:
    """Compile the harness, run scenarios, and emit a JSON functional summary."""
    failures: list[str] = []
    details: list[dict] = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        binary_path = tmp_path / "functional_harness"
        compile_harness(binary_path)

        with_in_progress = run_case(
            binary_path,
            "with_in_progress",
            tmp_path / "with_in_progress.txt",
        )
        without_in_progress = run_case(
            binary_path,
            "without_in_progress",
            tmp_path / "without_in_progress.txt",
        )
        sequence = run_case(
            binary_path,
            "sequence",
            tmp_path / "sequence_a.txt",
            tmp_path / "sequence_b.txt",
        )

    expected_with_in_progress = (
        DATA_DIR / "expected_packet_with_in_progress.txt"
    ).read_text()
    expected_without_in_progress = (
        DATA_DIR / "expected_packet_without_in_progress.txt"
    ).read_text()

    expect_equal(
        "preview/save with in-progress tote",
        with_in_progress["preview"],
        expected_with_in_progress,
        failures,
    )
    expect_equal(
        "saved packet with in-progress tote",
        with_in_progress["saved"],
        expected_with_in_progress,
        failures,
    )
    expect_true(
        "in-progress tote flag missing",
        with_in_progress["last_row_in_progress"] is True,
        failures,
    )
    expect_true(
        "with-in-progress summary mismatch",
        with_in_progress["tote_count"] == 3 and with_in_progress["package_count"] == 9,
        failures,
    )

    expect_equal(
        "preview/save without in-progress tote",
        without_in_progress["preview"],
        expected_without_in_progress,
        failures,
    )
    expect_equal(
        "saved packet without in-progress tote",
        without_in_progress["saved"],
        expected_without_in_progress,
        failures,
    )
    expect_true(
        "without-in-progress flag incorrect",
        without_in_progress["last_row_in_progress"] is False,
        failures,
    )
    expect_true(
        "without-in-progress summary mismatch",
        without_in_progress["tote_count"] == 3
        and without_in_progress["package_count"] == 8,
        failures,
    )

    expect_equal(
        "preview sequence stability",
        sequence["preview_first"],
        sequence["preview_second"],
        failures,
    )
    expect_equal(
        "save sequence stability",
        sequence["saved_first"],
        sequence["saved_second"],
        failures,
    )
    expect_equal(
        "preview/save order consistency",
        sequence["preview_first"],
        sequence["saved_first"],
        failures,
    )
    expect_true(
        "sequence row count changed",
        sequence["row_count_first"] == sequence["row_count_second"] == 3,
        failures,
    )
    expect_true(
        "sequence package count changed",
        sequence["package_count_first"] == sequence["package_count_second"] == 9,
        failures,
    )

    details.extend([with_in_progress, without_in_progress, sequence])

    summary = {
        "suite": "functional",
        "passed": not failures,
        "failures": failures,
        "details": details,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
