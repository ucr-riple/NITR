#!/usr/bin/env python3

from pathlib import Path
import re
import sys


CASE_REL = Path("cases/018.seeded-selection-testability")


def grep(pattern: str, *paths: Path):
    """Yield files whose contents match the given regex under the provided paths."""
    compiled = re.compile(pattern, re.MULTILINE)
    for path in paths:
        if path.is_dir():
            for file_path in sorted(path.rglob("*")):
                if file_path.suffix not in {".h", ".cc"}:
                    continue
                text = file_path.read_text(encoding="utf-8", errors="replace")
                if compiled.search(text):
                    yield file_path
        elif path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            if compiled.search(text):
                yield path


def fail(msg: str) -> int:
    """Print a failure message and return the evaluator's failing exit code."""
    print(msg)
    return 1


def main() -> int:
    """Reject test-only hooks and nondeterministic selection mechanisms in src/."""
    case_root = Path.cwd() / CASE_REL
    src_dir = case_root / "src"

    if list(grep(r"test_mode|ForceNextPick|force_next_pick|debug_only", src_dir)):
        return fail("Forbidden test-only control hook found in src/")

    if list(
        grep(
            r"static\s+std::(mt19937|default_random_engine)|global.*rng|singleton.*rng",
            src_dir,
        )
    ):
        return fail("Potential global mutable RNG pattern found")

    if list(grep(r"sleep_for|sleep_until|std::chrono|time\(|clock\(", src_dir)):
        return fail("Time/sleep-based nondeterminism detected in src/")

    if list(grep(r"seed|sampler|replay", src_dir / "candidate.h")):
        return fail("Seed/replay control leaked into candidate model header")

    selector_text = (src_dir / "selector.cc").read_text(
        encoding="utf-8", errors="replace"
    )
    if "SamplerV1" not in selector_text:
        return fail("Replay path does not appear to use SamplerV1 contract")

    print("All structural checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
