#!/usr/bin/env python3

import argparse
from pathlib import Path

from evaluator.shared.path_checks import (
    case_root_from_script,
    read_text,
)
from evaluator.shared.source_analysis import find_matching_paths
from evaluator.shared.check_output import emit_check_result, fail_message


def main() -> int:
    """Reject test-only hooks and nondeterministic selection mechanisms in src/."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    src_dir = case_root / "src"

    if find_matching_paths(
        r"test_mode|ForceNextPick|force_next_pick|debug_only", src_dir
    ):
        return fail_message("Forbidden test-only control hook found in src/")

    if find_matching_paths(
        r"static\s+std::(mt19937|default_random_engine)|global.*rng|singleton.*rng",
        src_dir,
    ):
        return fail_message("Potential global mutable RNG pattern found")

    if find_matching_paths(
        r"sleep_for|sleep_until|std::chrono|time\(|clock\(", src_dir
    ):
        return fail_message("Time/sleep-based nondeterminism detected in src/")

    if find_matching_paths(r"seed|sampler|replay", src_dir / "candidate.h"):
        return fail_message("Seed/replay control leaked into candidate model header")

    selector_text = read_text(
        src_dir / "selector.cc",
        encoding="utf-8",
        errors="replace",
        missing_ok=False,
    )
    if "SamplerV1" not in selector_text:
        return fail_message("Replay path does not appear to use SamplerV1 contract")

    return emit_check_result(passed=True, findings=[])


if __name__ == "__main__":
    raise SystemExit(main())
