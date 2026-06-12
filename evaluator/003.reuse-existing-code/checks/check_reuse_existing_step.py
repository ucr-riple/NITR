#!/usr/bin/env python3

import argparse
import re
import sys
from pathlib import Path

from evaluator.shared.check_utils import case_root_from_script, read_text


def fail(message: str) -> int:
    print(message)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", type=Path, default=case_root_from_script(__file__))
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    path = case_root / "src" / "cosine_similarity.cc"
    code = read_text(path)
    if not code:
        return fail(f"Failed to read {path}")

    required_patterns = {
        '#include "dot_product.h"': re.compile(r'#include\s+"dot_product\.h"'),
        '#include "l2_norm.h"': re.compile(r'#include\s+"l2_norm\.h"'),
        "DotProduct(...) call": re.compile(r"(?:nitr::case003::)?DotProduct\s*\("),
        "L2Norm(...) call": re.compile(r"(?:nitr::case003::)?L2Norm\s*\("),
    }
    for description, pattern in required_patterns.items():
        if not pattern.search(code):
            return fail(f"Structural reuse check failed: missing {description} in src/cosine_similarity.cc")

    forbidden_patterns = [
        re.compile(r"\bsqrt\s*\("),
        re.compile(r"sum_sq\s*\+="),
        re.compile(r"sum\s*\+=\s*[^;]*\*[^;]*;"),
    ]
    if any(pattern.search(code) for pattern in forbidden_patterns):
        return fail(
            "Structural check failed: detected likely re-implementation of math utilities in src/cosine_similarity.cc"
        )

    print("Structural reuse check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
