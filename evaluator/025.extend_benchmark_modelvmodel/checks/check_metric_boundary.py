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
    metric_candidates = [
        path for path in src_root.glob("*metric*.*")
        if path.suffix in {".h", ".cc", ".hpp", ".cpp"}
    ]

    failures: list[str] = []

    if not metric_candidates:
        failures.append(
            "Expected metric-specific source or header files under src/."
        )

    if re.search(r"\baverage_precision\b\s*[*\/+-]\s*\bfps\b", runner_text):
        failures.append(
            "benchmark_runner.cc should not compute metric formulas directly."
        )

    if re.search(r"\bfps\b\s*[*\/+-]\s*\baverage_precision\b", runner_text):
        failures.append(
            "benchmark_runner.cc should not compute metric formulas directly."
        )

    if re.search(r"\bspeed_adjusted\s*=", runner_text):
        failures.append(
            "benchmark_runner.cc should orchestrate benchmark flow, not assign "
            "speed-adjusted scores inline."
        )

    metric_text = "\n".join(read_text(path) for path in metric_candidates)
    metric_text = strip_comments_and_strings(metric_text)

    if metric_candidates and not re.search(
        r"\baverage_precision\b\s*\*\s*\bfps\b|\bfps\b\s*\*\s*\baverage_precision\b",
        metric_text,
    ):
        failures.append(
            "Expected the speed-adjusted formula to live in a metric-focused file."
        )

    if failures:
        print("Metric boundary check failed:")
        for failure in failures:
            print(f"- {failure}")
        print(
            "Keep benchmark_runner focused on procedure and move score formulas "
            "behind metric-focused code."
        )
        return 1

    print("Metric boundary check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
