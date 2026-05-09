#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def strip_comments_and_strings(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    text = re.sub(r"'(?:\\.|[^'\\])+'", "''", text)
    return text


def main() -> int:
    if len(sys.argv) > 1:
        case_root = Path(sys.argv[1]).resolve()
    else:
        repo_root = Path(__file__).resolve().parents[3]
        case_root = repo_root / "cases" / "025.extend_benchmark_modelvmodel"

    src_root = case_root / "src"
    runner_text = strip_comments_and_strings(read_text(src_root / "benchmark_runner.cc"))
    record_text = strip_comments_and_strings(read_text(src_root / "benchmark_record.h"))
    data_text = strip_comments_and_strings(read_text(src_root / "benchmark_data.cc"))

    failures: list[str] = []

    if re.search(r"\baverage_precision\b", runner_text) or re.search(
        r"\bfps\b", runner_text
    ):
        failures.append(
            "benchmark_runner.cc should not inspect raw benchmark fields such "
            "as average_precision or fps."
        )

    if re.search(r"\baverage_precision\b\s*[*\/+-]\s*\bfps\b", runner_text) or re.search(
        r"\bfps\b\s*[*\/+-]\s*\baverage_precision\b", runner_text
    ):
        failures.append(
            "benchmark_runner.cc should not compute score formulas directly."
        )

    if re.search(r"\bD-FINE\b|\bRT-DETR\b", runner_text):
        failures.append(
            "benchmark_runner.cc should not special-case concrete model families."
        )

    if re.search(r"\bspeed_?adjusted\b", record_text):
        failures.append(
            "BenchmarkRecord should stay raw input data and not store derived "
            "speed-adjusted scores."
        )

    if re.search(r"\bspeed_?adjusted\b", data_text):
        failures.append(
            "benchmark_data.cc should contain source benchmark facts, not "
            "precomputed derived scores."
        )

    if failures:
        print("Benchmark responsibility check failed:")
        for failure in failures:
            print(f"- {failure}")
        print(
            "Keep benchmark_runner focused on orchestration, keep benchmark "
            "rows raw, and place derived score computation behind a helper or "
            "component outside the runner."
        )
        return 1

    print("Benchmark responsibility check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
