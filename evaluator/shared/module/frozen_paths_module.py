#!/usr/bin/env python3

"""Frozen-path evaluation module."""

from __future__ import annotations

from evaluator.shared.context import EvaluationContext
from evaluator.shared.module.base import EvaluationModule
from evaluator.shared.module.result import ModuleResult
from evaluator.shared.module.path_checks import classify_relative_paths_against_baseline


class FrozenPathsModule(EvaluationModule):
    module_name = "frozen_paths"

    def evaluate(self, context: EvaluationContext) -> ModuleResult:
        baseline_root = self._require_baseline(context)
        relative_paths = self.config.get("paths", [])
        if not relative_paths:
            raise ValueError(f"Module '{self.name}' requires a non-empty 'paths' list")

        status = classify_relative_paths_against_baseline(
            context.case_root, baseline_root, relative_paths
        )
        findings: list[str] = []
        findings.extend(
            f"Frozen path missing from case root: {path}"
            for path in status.missing_in_root
        )
        findings.extend(
            f"Frozen path missing from baseline root: {path}"
            for path in status.missing_in_baseline
        )
        findings.extend(
            f"Frozen path unexpectedly created: {path}"
            for path in status.created_in_root
        )
        findings.extend(
            f"Frozen path unexpectedly deleted: {path}"
            for path in status.deleted_from_root
        )
        findings.extend(
            f"Frozen path unexpectedly modified: {path}" for path in status.modified
        )

        return self._base_result(
            passed=not findings,
            findings=findings,
            details={"checked_paths": list(relative_paths)},
        )
