#!/usr/bin/env python3

"""Shared evaluator helpers grouped by check intent.

1. File existence / retention
2. File creation / touch boundaries
3. File content stability / freeze checks

Structural / semantic signal checks live in `evaluator.shared.module.source_analysis`.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

CPP_LIKE_SUFFIXES = (".h", ".hpp", ".hh", ".cc", ".cpp", ".cxx")
RelativePathLike = str | Path


@dataclass(frozen=True)
class BaselinePathCheck:
    missing_in_root: list[str]
    missing_in_baseline: list[str]
    created_in_root: list[str]
    deleted_from_root: list[str]
    modified: list[str]


# Shared path / repo context
def repo_root_from_script(script_path: str | Path) -> Path:
    return Path(script_path).resolve().parents[3]


def case_name_from_script(script_path: str | Path) -> str:
    return Path(script_path).resolve().parents[1].name


def case_root_from_script(script_path: str | Path) -> Path:
    return (
        repo_root_from_script(script_path)
        / "cases"
        / case_name_from_script(script_path)
    )


def evaluator_root_from_script(script_path: str | Path) -> Path:
    return (
        repo_root_from_script(script_path)
        / "evaluator"
        / case_name_from_script(script_path)
    )


# Shared file IO
def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def read_text(
    path: Path,
    *,
    encoding: str = "utf-8",
    errors: str | None = None,
    missing_ok: bool = True,
) -> str:
    if missing_ok and not path.exists():
        return ""
    kwargs = {"encoding": encoding}
    if errors is not None:
        kwargs["errors"] = errors
    return path.read_text(**kwargs)


# 1. File existence / retention
def find_missing_paths(paths: Iterable[Path]) -> list[Path]:
    return [path for path in paths if not path.exists()]


def _to_relative_path(path: RelativePathLike) -> Path:
    return path if isinstance(path, Path) else Path(path)


def find_missing_relative_paths(
    root: Path, relative_paths: Iterable[RelativePathLike]
) -> list[str]:
    missing: list[str] = []
    for relative_path in relative_paths:
        rel = _to_relative_path(relative_path)
        if not (root / rel).exists():
            missing.append(rel.as_posix())
    return missing


def find_deleted_relative_paths(
    root: Path, baseline_root: Path, relative_paths: Iterable[RelativePathLike]
) -> list[str]:
    deleted: list[str] = []
    for relative_path in relative_paths:
        rel = _to_relative_path(relative_path)
        if not (root / rel).exists() and (baseline_root / rel).exists():
            deleted.append(rel.as_posix())
    return deleted


# 2. File creation / touch boundaries
def find_new_relative_paths(
    root: Path, baseline_root: Path, relative_paths: Iterable[RelativePathLike]
) -> list[str]:
    created: list[str] = []
    for relative_path in relative_paths:
        rel = _to_relative_path(relative_path)
        if (root / rel).exists() and not (baseline_root / rel).exists():
            created.append(rel.as_posix())
    return created


def find_paths_with_disallowed_top_level(
    paths: Iterable[RelativePathLike], allowed_top_levels: Iterable[str]
) -> list[str]:
    allowed = set(allowed_top_levels)
    violations: list[str] = []
    for raw_path in paths:
        rel = _to_relative_path(raw_path)
        top = rel.parts[0] if rel.parts else ""
        if top not in allowed:
            violations.append(rel.as_posix())
    return violations


def find_relative_paths_not_in_allowlist(
    paths: Iterable[RelativePathLike],
    allowed_relative_paths: Iterable[RelativePathLike],
) -> list[str]:
    allowed = {_to_relative_path(path).as_posix() for path in allowed_relative_paths}
    violations: list[str] = []
    for raw_path in paths:
        rel = _to_relative_path(raw_path).as_posix()
        if rel not in allowed:
            violations.append(rel)
    return violations


def scan_files(*roots: Path, suffixes: Iterable[str] = CPP_LIKE_SUFFIXES) -> list[Path]:
    if not roots:
        return []
    suffix_set = set(suffixes)
    return sorted(
        {
            path
            for root in roots
            for path in root.rglob("*")
            if path.is_file() and path.suffix in suffix_set
        }
    )


# 3. File content stability / freeze checks
def find_modified_relative_paths(
    root: Path, baseline_root: Path, relative_paths: Iterable[RelativePathLike]
) -> list[str]:
    modified: list[str] = []
    for relative_path in relative_paths:
        rel = _to_relative_path(relative_path)
        if (root / rel).read_bytes() != (baseline_root / rel).read_bytes():
            modified.append(rel.as_posix())
    return modified


def classify_relative_paths_against_baseline(
    root: Path, baseline_root: Path, relative_paths: Iterable[RelativePathLike]
) -> BaselinePathCheck:
    """Compare a fixed set of relative paths between a case root and baseline root.

    Args:
        root: Current case root to validate.
        baseline_root: Baseline/starter case root used for comparison.
        relative_paths: Relative paths to classify against the two roots.

    Returns structured path status for the supplied relative paths, including:
    - paths missing from the current root
    - paths missing from the baseline root
    - paths newly created in the current root
    - paths deleted from the current root relative to baseline
    - paths present in both roots whose bytes differ
    """
    relative_paths = list(relative_paths)
    missing = find_missing_relative_paths(root, relative_paths)
    missing_baseline = find_missing_relative_paths(baseline_root, relative_paths)
    created = find_new_relative_paths(root, baseline_root, relative_paths)
    deleted = find_deleted_relative_paths(root, baseline_root, relative_paths)
    comparable = [
        relative_path
        for relative_path in relative_paths
        if _to_relative_path(relative_path).as_posix() not in missing
        and _to_relative_path(relative_path).as_posix() not in missing_baseline
    ]
    modified = find_modified_relative_paths(root, baseline_root, comparable)
    return BaselinePathCheck(
        missing_in_root=missing,
        missing_in_baseline=missing_baseline,
        created_in_root=created,
        deleted_from_root=deleted,
        modified=modified,
    )
