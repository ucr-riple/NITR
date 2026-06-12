#!/usr/bin/env python3
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from evaluator.shared.check_utils import case_root_from_script, read_text, sha256

ROOT = case_root_from_script(__file__)

EXPECTED_HASHES = {
    "src/feature_transform.h": "73f6067d946fafff153d1ff9fc72f10bd6f7934efbe0fc0ee90ef4213dea4570",
    "src/feature_pipeline.h": "095c9b09d68ccb459ee2a667cf10073f5b69fe8e22457eaa7105b7f7cefefa41",
    "src/feature_pipeline.cc": "458fc454940fe878a1c761f73c6074fbd6d3458af4f97c55f63656e8817aec87",
}

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
    ok = True
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            print(f"missing required file: {rel}")
            ok = False
    for rel, expected in EXPECTED_HASHES.items():
        path = ROOT / rel
        if not path.exists():
            print(f"missing protected file: {rel}")
            ok = False
            continue
        actual = sha256(path)
        if actual != expected:
            print(f"protected file modified: {rel}")
            ok = False
    for path in ROOT.glob("src/*"):
        if path.suffix not in {".h", ".cc"}:
            continue
        text = read_text(path, missing_ok=False)
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in text:
                print(f"forbidden pattern {pattern} found in {path.relative_to(ROOT)}")
                ok = False
    for rel in GENERIC_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        text = read_text(path, missing_ok=False)
        for token in CONCRETE_TOKENS:
            if token in text:
                print(f"generic path leaked concrete type {token} in {rel}")
                ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
