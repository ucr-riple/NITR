#!/usr/bin/env python3

"""Compare a generated case tree against its baseline counterpart.

This module enforces file-boundary constraints by diffing the current case root
against `baseline_case_root`. It is useful when a task is only supposed to
touch a small, explicit subset of files, or when certain paths must not be
created, deleted, or modified relative to the starter code.

Typical use cases:
- freezing most of `src/` while allowing edits in one implementation file
- allowing new files only under selected top-level directories
- enforcing that starter app wiring files remain unchanged

Configuration shape:
- `module_name`: must be `"baseline_diff"`
- `name`: human-readable module instance name used in reports
- either:
  - `paths`: explicit relative paths to compare, or
  - `include_globs`: file globs collected from both current and baseline roots
- `exclude_globs`: optional paths/globs to ignore
- `allow_created`: optional explicit allowlist for newly created files
- `allow_deleted`: optional explicit allowlist for deleted files
- `allow_modified`: optional explicit allowlist for modified files
- `allow_missing_in_root`: optional allowlist for paths absent from case root
- `allow_missing_in_baseline`: optional allowlist for paths absent from baseline
- `allowed_created_top_levels`: optional top-level directory allowlist for new files

Execution behavior:
- requires `baseline_case_root` in the evaluation context
- collects the target file set from `paths` or `include_globs`
- classifies each path as missing, created, deleted, or modified
- reports any change not covered by the configured allowlists

This module is broader than `frozen_paths`: it supports partial allowlists and
glob-driven collection instead of enforcing a strict no-change policy for a
fixed path list.
"""

from __future__ import annotations

from pathlib import Path

from evaluator.shared.context import EvaluationContext
from evaluator.shared.module.base import EvaluationModule
from evaluator.shared.module.result import ModuleResult
from evaluator.shared.module.path_checks import classify_relative_paths_against_baseline


class BaselineDiffModule(EvaluationModule):
    module_name = "baseline_diff"

    def evaluate(self, context: EvaluationContext) -> ModuleResult:
        baseline_root = self._require_baseline(context)
        relative_paths = self._collect_relative_paths(context, baseline_root)
        status = classify_relative_paths_against_baseline(
            context.case_root, baseline_root, relative_paths
        )

        allow_created = set(self.config.get("allow_created", []))
        allow_deleted = set(self.config.get("allow_deleted", []))
        allow_modified = set(self.config.get("allow_modified", []))
        allow_missing_in_root = set(self.config.get("allow_missing_in_root", []))
        allow_missing_in_baseline = set(self.config.get("allow_missing_in_baseline", []))
        allowed_created_top_levels = self.config.get("allowed_created_top_levels", [])

        findings: list[str] = []
        for path in status.missing_in_root:
            if path in status.deleted_from_root:
                continue
            if path not in allow_missing_in_root:
                findings.append(f"Path missing from case root: {path}")
        for path in status.missing_in_baseline:
            if path in status.created_in_root:
                continue
            if path not in allow_missing_in_baseline:
                findings.append(f"Path missing from baseline root: {path}")
        for path in status.created_in_root:
            if path in allow_created:
                continue
            if allowed_created_top_levels:
                top = Path(path).parts[0] if Path(path).parts else ""
                if top in set(allowed_created_top_levels):
                    continue
            findings.append(f"Unexpected new path in case root: {path}")
        for path in status.deleted_from_root:
            if path not in allow_deleted:
                findings.append(f"Unexpected deleted path from case root: {path}")
        for path in status.modified:
            if path not in allow_modified:
                findings.append(f"Unexpected modified path relative to baseline: {path}")

        return self._base_result(
            passed=not findings,
            findings=findings,
            details={
                "checked_paths": relative_paths,
                "case_root": context.case_root.as_posix(),
                "baseline_case_root": baseline_root.as_posix(),
            },
        )

    def _collect_relative_paths(
        self, context: EvaluationContext, baseline_root: Path
    ) -> list[str]:
        explicit_paths = self.config.get("paths")
        if explicit_paths:
            return [str(path) for path in explicit_paths]

        include_globs = self.config.get("include_globs", ["src/**/*", "app/**/*"])
        exclude_globs = set(self.config.get("exclude_globs", []))
        collected: set[str] = set()
        for root in (context.case_root, baseline_root):
            for pattern in include_globs:
                for candidate in root.glob(pattern):
                    if not candidate.is_file():
                        continue
                    relative = candidate.relative_to(root).as_posix()
                    if any(candidate.match(glob) for glob in exclude_globs):
                        continue
                    if any(Path(relative).match(glob) for glob in exclude_globs):
                        continue
                    collected.add(relative)
        return sorted(collected)
