#!/usr/bin/env python3
import argparse
import pathlib
import sys

from evaluator.shared.check_utils import (
    classify_relative_paths_against_baseline,
    case_root_from_script,
    find_missing_relative_paths,
    read_text,
)

ROOT = case_root_from_script(__file__)

PROTECTED_FILES = [
    "src/feature_transform.h",
    "src/feature_pipeline.h",
    "src/feature_pipeline.cc",
]

REQUIRED_FILES = [
    "src/clamp_transform.h",
    "src/clamp_transform.cc",
    "src/transform_batch.h",
    "src/transform_batch.cc",
    "src/transform_chain.h",
    "src/transform_chain.cc",
]

FORBIDDEN_PATTERNS = [
    "dynamic_cast",
    "typeid",
]

GENERIC_FILES = [
    "src/transform_batch.h",
    "src/transform_batch.cc",
    "src/transform_chain.h",
    "src/transform_chain.cc",
]

CONCRETE_TOKENS = [
    "ClampTransform",
    "IdentityTransform",
    "L2NormalizeTransform",
]

def main() -> int:
    """Validate protected files, required artifacts, and generic pipeline boundaries."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--baseline_case_root", type=pathlib.Path, default=ROOT)
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    baseline_root = args.baseline_case_root.resolve()

    ok = True
    for rel in find_missing_relative_paths(case_root, REQUIRED_FILES):
        print(f"missing required file: {rel}")
        ok = False

    protected_status = classify_relative_paths_against_baseline(
        case_root, baseline_root, PROTECTED_FILES
    )
    for rel in protected_status.missing_in_root:
        print(f"missing protected file: {rel}")
        ok = False

    for rel in protected_status.missing_in_baseline:
        print(f"missing baseline protected file: {rel}")
        ok = False

    for rel in protected_status.modified:
        print(f"protected file modified: {rel}")
        ok = False
    for path in case_root.glob("src/*"):
        if path.suffix not in {".h", ".cc"}:
            continue
        text = read_text(path, missing_ok=False)
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in text:
                print(
                    f"forbidden pattern {pattern} found in {path.relative_to(case_root)}"
                )
                ok = False
    for rel in GENERIC_FILES:
        path = case_root / rel
        if not path.exists():
            continue
        text = read_text(path, missing_ok=False)
        for token in CONCRETE_TOKENS:
            if token in text:
                print(f"generic path leaked concrete type {token} in {rel}")
                ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
