#!/usr/bin/env python3
"""Validate evaluator wiring consistency across the public NITR repository.

This checker performs a repo-wide static scan over evaluator case directories and
their corresponding registration logic in ``evaluator/CMakeLists.txt``.

Its goal is to catch public-evaluator wiring mistakes such as:
- evaluator-side test or check sources that exist on disk but are not wired into
  any CMake target or covered wrapper script
- Python check scripts that are only reachable through one evaluation path
- wrapper scripts such as ``checks/run_evaluator.py`` that exist but are never
  registered from CMake
- duplicate manual ``add_test(...)`` aliases that point to the same command

This script does not try to prove that starter baselines pass functional tests.
Instead, it focuses on whether the evaluator infrastructure itself is wired
coherently and whether expected evaluator files are reachable through the
repo-local public evaluation path.
"""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

from benchmark_check_utils import (
    EVALUATOR_ROOT,
    REPO_ROOT,
    discover_case_slugs,
    discover_evaluator_case_slugs,
    read_text,
)
from evaluator.shared.check_output import CHECK_FAILED, CHECK_PASSED


CMAKE_FILE = EVALUATOR_ROOT / "CMakeLists.txt"

SOURCE_EXTS = {".c", ".cc", ".cpp", ".cxx"}
HEADER_EXTS = {".h", ".hh", ".hpp", ".hxx"}
PY_EXTS = {".py"}

# Files intentionally present for hidden or auxiliary workflows but not required to be
# wired into the public CTest path.
IGNORED_RELATIVE_FILES = {
    "015.pipeline-provider-decoupling/checks/check_allowed_file_touches.py",
}


class FindingType(StrEnum):
    """Stable machine-readable categories for benchmark consistency findings."""

    DUPLICATE_TEST_COMMAND_ALIAS = "duplicate_test_command_alias"
    MISSING_CASE_REGISTRATION = "missing_case_registration"
    UNREGISTERED_CHECK_SCRIPT = "unregistered_check_script"
    UNREGISTERED_TEST_SCRIPT = "unregistered_test_script"
    UNREGISTERED_WRAPPER_SCRIPT = "unregistered_wrapper_script"
    UNWIRED_CHECK_SOURCE = "unwired_check_source"
    UNWIRED_TEST_SOURCE = "unwired_test_source"


@dataclass
class Finding:
    """One benchmark consistency problem reported by the repo-wide checker."""

    # Stable machine-readable category for this kind of issue.
    finding_type: FindingType
    # Case slug such as 005.pricing-ocp.
    case: str
    # Repository-relative file or location associated with the finding.
    path: str
    # Human-readable explanation of what is wrong.
    message: str


def load_case_function_bodies(cmake_text: str) -> dict[str, str]:
    """Map zero-padded case ids to the body text of nitr_register_case_* functions."""

    pattern = re.compile(
        r"function\(nitr_register_case_(\d+)\)\n(.*?)\nendfunction\(\)",
        re.DOTALL,
    )
    bodies: dict[str, str] = {}
    for match in pattern.finditer(cmake_text):
        bodies[match.group(1).zfill(3)] = match.group(2)
    return bodies


def case_id_from_slug(case_slug: str) -> str:
    """Extract the zero-padded numeric case id prefix from a case slug."""

    return case_slug.split(".", 1)[0]


def relative_to_case(case_dir: Path, path: Path) -> str:
    """Render a file path relative to its case evaluator directory."""

    return path.relative_to(case_dir).as_posix()


def path_token_present(text: str, relative_path: str) -> bool:
    """Check whether CMake or wrapper text references a file by relative path or basename."""

    filename = Path(relative_path).name
    return relative_path in text or filename in text


def discover_local_files(case_dir: Path) -> list[Path]:
    """Collect evaluator-side source and script files under tests/ and checks/ for one case."""

    files: list[Path] = []
    for group in ("tests", "checks"):
        root = case_dir / group
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix not in SOURCE_EXTS | HEADER_EXTS | PY_EXTS:
                continue
            files.append(path)
    return files


def build_transitive_python_coverage(
    case_dir: Path, initially_covered: set[str]
) -> set[str]:
    """Follow same-case references from covered Python entrypoints to local helper files."""
    all_files = {
        relative_to_case(case_dir, path): path
        for path in discover_local_files(case_dir)
    }
    covered = set(initially_covered)
    queue = [
        rel for rel in initially_covered if all_files.get(rel, Path()).suffix == ".py"
    ]

    while queue:
        rel = queue.pop()
        path = all_files.get(rel)
        if path is None or path.suffix != ".py":
            continue

        text = read_text(path)
        for candidate_rel, candidate_path in all_files.items():
            if candidate_rel in covered:
                continue
            if path_token_present(text, candidate_rel):
                covered.add(candidate_rel)
                if candidate_path.suffix == ".py":
                    queue.append(candidate_rel)

    return covered


def find_duplicate_manual_test_commands(
    case_slug: str, case_body: str
) -> list[Finding]:
    """Report manually duplicated add_test command aliases within one case registration."""

    command_to_names: dict[str, list[str]] = {}
    pattern = re.compile(
        r"add_test\(\s*NAME\s+([^\s\)]+)\s+COMMAND\s+([^\s\)]+)",
        re.DOTALL,
    )
    for match in pattern.finditer(case_body):
        test_name = match.group(1)
        command = match.group(2)
        if command == "${Python3_EXECUTABLE}":
            continue
        command_to_names.setdefault(command, []).append(test_name)

    findings: list[Finding] = []
    for command, names in sorted(command_to_names.items()):
        unique_names = sorted(set(names))
        if len(unique_names) < 2:
            continue
        findings.append(
            Finding(
                finding_type=FindingType.DUPLICATE_TEST_COMMAND_ALIAS,
                case=case_slug,
                path=str(CMAKE_FILE.relative_to(REPO_ROOT)),
                message=(
                    f"manual add_test registers command '{command}' under multiple names: "
                    + ", ".join(unique_names)
                ),
            ),
        )
    return findings


def check_case(case_dir: Path, case_body: str) -> list[Finding]:
    """Run file-discovery and wiring checks for one evaluator case directory."""

    case_slug = case_dir.name
    files = discover_local_files(case_dir)
    direct_covered = {
        relative_to_case(case_dir, path)
        for path in files
        if path_token_present(case_body, relative_to_case(case_dir, path))
    }
    covered = build_transitive_python_coverage(case_dir, direct_covered)

    findings: list[Finding] = []
    findings.extend(find_duplicate_manual_test_commands(case_slug, case_body))

    for path in files:
        rel = relative_to_case(case_dir, path)
        repo_rel = f"{case_slug}/{rel}"
        if repo_rel in IGNORED_RELATIVE_FILES:
            continue

        if path.suffix in HEADER_EXTS:
            continue

        # Classify by top-level bucket under the case evaluator tree so nested
        # paths like checks/inject/injected_rule.cc still count as "checks".
        rel_parts = Path(rel).parts
        group = rel_parts[0] if rel_parts else ""
        is_covered = rel in covered

        if group == "tests" and path.suffix in SOURCE_EXTS and not is_covered:
            findings.append(
                Finding(
                    finding_type=FindingType.UNWIRED_TEST_SOURCE,
                    case=case_slug,
                    path=str(path.relative_to(REPO_ROOT)),
                    message="test source exists but is not referenced from CMake or a covered local wrapper script",
                )
            )
            continue

        if group == "checks" and path.suffix in SOURCE_EXTS and not is_covered:
            findings.append(
                Finding(
                    finding_type=FindingType.UNWIRED_CHECK_SOURCE,
                    case=case_slug,
                    path=str(path.relative_to(REPO_ROOT)),
                    message="check-side C/C++ source exists but is not referenced from CMake or a covered local wrapper script",
                )
            )
            continue

        if path.suffix not in PY_EXTS:
            continue

        if rel == "checks/run_evaluator.py":
            if not is_covered:
                findings.append(
                    Finding(
                        finding_type=FindingType.UNREGISTERED_WRAPPER_SCRIPT,
                        case=case_slug,
                        path=str(path.relative_to(REPO_ROOT)),
                        message="wrapper evaluator script exists but is not referenced from CMake",
                    )
                )
            continue

        if group == "checks" and not is_covered:
            findings.append(
                Finding(
                    finding_type=FindingType.UNREGISTERED_CHECK_SCRIPT,
                    case=case_slug,
                    path=str(path.relative_to(REPO_ROOT)),
                    message="Python check exists but is not covered by CTest registration or a covered wrapper script",
                )
            )
            continue

        if group == "tests" and not is_covered:
            findings.append(
                Finding(
                    finding_type=FindingType.UNREGISTERED_TEST_SCRIPT,
                    case=case_slug,
                    path=str(path.relative_to(REPO_ROOT)),
                    message="Python test/helper script exists but is not covered by CTest registration or a covered wrapper script",
                )
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check evaluator wiring consistency across NITR benchmark cases."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of plain text.",
    )
    args = parser.parse_args()

    cmake_text = read_text(CMAKE_FILE)
    case_bodies = load_case_function_bodies(cmake_text)

    findings: list[Finding] = []
    case_slug_set = set(discover_case_slugs())
    for case_slug in discover_evaluator_case_slugs():
        if case_slug in case_slug_set:
            continue
        findings.append(
            Finding(
                finding_type=FindingType.MISSING_CASE_REGISTRATION,
                case=case_slug,
                path=str((EVALUATOR_ROOT / case_slug).relative_to(REPO_ROOT)),
                message="evaluator case directory exists without a matching cases/ entry",
            )
        )

    for case_slug in discover_case_slugs():
        case_dir = EVALUATOR_ROOT / case_slug
        if not case_dir.is_dir():
            continue
        case_id = case_id_from_slug(case_slug)
        case_body = case_bodies.get(case_id)
        if case_body is None:
            findings.append(
                Finding(
                    finding_type=FindingType.MISSING_CASE_REGISTRATION,
                    case=case_slug,
                    path=str(case_dir.relative_to(REPO_ROOT)),
                    message="evaluator case directory exists but no nitr_register_case_* function was found",
                )
            )
            continue
        findings.extend(check_case(case_dir, case_body))

    if args.json:
        print(
            json.dumps(
                {
                    "ok": not findings,
                    "finding_count": len(findings),
                    "findings": [asdict(finding) for finding in findings],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        if not findings:
            print("Benchmark consistency check passed.")
        else:
            print(f"Benchmark consistency check found {len(findings)} issue(s):")
            for finding in findings:
                print(
                    f"- [{finding.finding_type}] {finding.case} {finding.path}: {finding.message}"
                )

    return CHECK_PASSED if not findings else CHECK_FAILED


if __name__ == "__main__":
    sys.exit(main())
