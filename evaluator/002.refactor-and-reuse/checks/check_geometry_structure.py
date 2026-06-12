#!/usr/bin/env python3

import pathlib
import re
import sys

from evaluator.shared.check_utils import extract_function_body, strip_comments_and_strings


ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.cwd()
SRC = ROOT / "src" / "geometry.cc"


def count_hits(patterns, text: str) -> int:
    """Count how many structural evidence patterns appear in the source text."""
    hits = 0
    for pattern in patterns:
        if re.search(pattern, text):
            hits += 1
    return hits


def main() -> int:
    code = strip_comments_and_strings(SRC.read_text(encoding="utf-8"))
    fundamental_body = extract_function_body(code, "EstimateFundamental8Point")
    essential_body = extract_function_body(code, "EstimateEssential8Point")

    if not fundamental_body:
        print("Missing EstimateFundamental8Point body")
        return 1

    if not essential_body:
        print("Missing EstimateEssential8Point body")
        return 1

    normalization_patterns = [
        r"\bmean_[xy]\b",
        r"\bcentroid\b",
        r"sqrt\s*\(\s*2(?:\.0)?\s*\)",
        r"\bscale\b",
        r"\bT1\b",
        r"\bT2\b",
        r"transpose\s*\(\s*\)\s*\*.*\*",
    ]

    normalization_hits = count_hits(normalization_patterns, code)
    if normalization_hits < 3:
        print("Expected Hartley-style normalization evidence in src/geometry.cc")
        return 1

    essential_constraint_patterns = [
        r"\w+\s*\(\s*0\s*\)\s*=\s*\w+\s*\(\s*1\s*\)",
        r"\w+\s*\(\s*1\s*\)\s*=\s*\w+\s*\(\s*0\s*\)",
        r"\w+\s*\[\s*0\s*\]\s*=\s*\w+\s*\[\s*1\s*\]",
        r"\w+\s*\[\s*1\s*\]\s*=\s*\w+\s*\[\s*0\s*\]",
        r"(?:Vector3d|Diagonal|DiagonalMatrix)\s*\(\s*1(?:\.0)?\s*,\s*1(?:\.0)?\s*,\s*0(?:\.0)?\s*\)",
        r"\bJacobiSVD\b[\s\S]*?\bsingularValues\b",
        r"\bsingularValues\b.*=.*\b1(?:\.0)?\s*,\s*1(?:\.0)?\s*,\s*0(?:\.0)?",
        r"\b\w+\s*<<\s*\w+\s*,\s*\w+\s*,\s*0(?:\.0)?\b",
        r"\b\w+\s*=\s*0\.5\s*\*\s*\(\s*\w+\s*\(\s*0\s*\)\s*\+\s*\w+\s*\(\s*1\s*\)\s*\)",
    ]

    essential_hits = count_hits(essential_constraint_patterns, code)
    if essential_hits == 0:
        print(
            "Expected essential-matrix singular value constraint handling in src/geometry.cc"
        )
        return 1

    if "return Solve8Point" in essential_body and essential_hits == 0:
        print(
            "Essential path appears to reuse the fundamental solve without essential-specific post-processing"
        )
        return 1

    print("geometry structure checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
