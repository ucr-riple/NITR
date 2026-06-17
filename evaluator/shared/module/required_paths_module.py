#!/usr/bin/env python3

"""Require specific files or directories to exist under a chosen root.

This module is a lightweight existence check. It is useful for cases that ask
the model to introduce new source files, headers, tests, or other artifacts as
part of the expected solution shape.

Typical use cases:
- requiring a newly extracted header/source pair to be present
- checking that expected support files were added under `src/` or `app/`
- enforcing that a case created named output artifacts before deeper analysis

Configuration shape:
- `module_name`: must be `"required_paths"`
- `name`: human-readable module instance name used in reports
- `root`: optional symbolic root selector such as `case_root`; defaults to
  `"case_root"`
- `paths`: required non-empty list of relative paths expected under that root

Execution behavior:
- resolves the configured root from the evaluation context
- checks each configured relative path for existence
- reports every missing path as a failure

This module only checks presence. It does not validate contents, ownership, or
whether a path changed relative to baseline; those concerns belong in other
modules such as `source_analysis` or `baseline_diff`.
"""

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
