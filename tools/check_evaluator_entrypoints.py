#!/usr/bin/env python3
"""Validate per-case evaluator entrypoints without requiring green baselines.

This checker iterates over every case under ``cases/`` and verifies that the
public evaluator path can at least be configured and discovered correctly:

- ``cmake`` must succeed with ``-DNITR_BUILD_EVALUATOR=ON`` for the case
- ``ctest -N --show-only=json-v1`` must discover at least one case-specific
  test entrypoint beyond repo-global checks such as ``nitr_format_check``

This script is intentionally lighter than a full batch evaluator run. It does
not require the case starter implementation to pass functional or structural
tests. Many NITR cases are intentionally incomplete at baseline, so failures in
the evaluated behavior are expected. The purpose here is narrower: distinguish
expected starter-state failures from evaluator infrastructure failures such as
missing registration or broken configuration paths.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from benchmark_check_utils import REPO_ROOT, discover_case_slugs, run_command


IGNORED_TEST_NAMES = {"nitr_format_check"}


@dataclass
class CaseResult:
    """One case-level evaluator entrypoint validation result."""

    case: str
    configure_ok: bool
    discover_ok: bool
    discovered_tests: list[str]
    message: str


def relevant_test_names(build_dir: Path) -> tuple[bool, list[str], str]:
    """Ask CTest for discovered tests and filter out repo-global checks."""

    proc = run_command(
        ["ctest", "--test-dir", str(build_dir), "-N", "--show-only=json-v1"],
        REPO_ROOT,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "ctest discovery failed"
        return False, [], detail

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        return False, [], f"failed to parse ctest JSON output: {error}"

    names = [
        test["name"]
        for test in payload.get("tests", [])
        if "name" in test and test["name"] not in IGNORED_TEST_NAMES
    ]
    if not names:
        return False, [], "no case-specific tests discovered"

    return True, names, "ok"


def check_case(case_slug: str, build_root: Path) -> CaseResult:
    """Configure one case with evaluator enabled and verify CTest discovers tests."""

    build_dir = build_root / case_slug
    if build_dir.resolve() == REPO_ROOT:
        return CaseResult(
            case=case_slug,
            configure_ok=False,
            discover_ok=False,
            discovered_tests=[],
            message="refusing to delete repository root as a build directory",
        )
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.parent.mkdir(parents=True, exist_ok=True)

    configure_cmd = [
        "cmake",
        "-S",
        str(REPO_ROOT),
        "-B",
        str(build_dir),
        "-DNITR_BUILD_ALL_CASES=OFF",
        f"-DNITR_CASE={case_slug}",
        "-DNITR_BUILD_EVALUATOR=ON",
    ]
    proc = run_command(configure_cmd, REPO_ROOT)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "cmake configure failed"
        return CaseResult(
            case=case_slug,
            configure_ok=False,
            discover_ok=False,
            discovered_tests=[],
            message=detail,
        )

    discover_ok, names, message = relevant_test_names(build_dir)
    return CaseResult(
        case=case_slug,
        configure_ok=True,
        discover_ok=discover_ok,
        discovered_tests=names,
        message=message,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check that each NITR case can configure with evaluator enabled and "
            "register at least one case-specific CTest entrypoint."
        )
    )
    parser.add_argument(
        "--build-root",
        help=(
            "Optional directory for per-case configure outputs. Existing "
            "<build-root>/<case-slug> directories may be deleted and recreated. "
            "Defaults to a temporary directory."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary.",
    )
    args = parser.parse_args()

    temp_dir = None
    if args.build_root:
        build_root = Path(args.build_root).resolve()
        build_root.mkdir(parents=True, exist_ok=True)
    else:
        temp_dir = tempfile.TemporaryDirectory(prefix="nitr_entrypoints_")
        build_root = Path(temp_dir.name)

    try:
        results = [check_case(case_slug, build_root) for case_slug in discover_case_slugs()]
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()

    failed = [result for result in results if not (result.configure_ok and result.discover_ok)]

    if args.json:
        print(
            json.dumps(
                {
                    "ok": not failed,
                    "case_count": len(results),
                    "failed_case_count": len(failed),
                    "results": [asdict(result) for result in results],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        if not failed:
            print("Evaluator entrypoint check passed.")
        else:
            print(f"Evaluator entrypoint check found {len(failed)} issue(s):")
            for result in failed:
                print(f"- {result.case}: {result.message}")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
