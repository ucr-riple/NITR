#!/usr/bin/env python3

"""Required-path evaluation module."""

from __future__ import annotations

from evaluator.shared.context import EvaluationContext
from evaluator.shared.module.base import EvaluationModule
from evaluator.shared.module.result import ModuleResult
from evaluator.shared.module.path_checks import find_missing_relative_paths


class RequiredPathsModule(EvaluationModule):
    module_name = "required_paths"

    def evaluate(self, context: EvaluationContext) -> ModuleResult:
        root = self._resolve_root(self.config.get("root", "case_root"), context)
        relative_paths = self.config.get("paths", [])
        if not relative_paths:
            raise ValueError(f"Module '{self.name}' requires a non-empty 'paths' list")

        missing = find_missing_relative_paths(root, relative_paths)
        findings = [f"Missing required path under {root}: {path}" for path in missing]
        return self._base_result(
            passed=not findings,
            findings=findings,
            details={"root": root.as_posix(), "checked_paths": list(relative_paths)},
        )
