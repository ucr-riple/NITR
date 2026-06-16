#!/usr/bin/env python3

"""Base class for config-driven evaluation modules."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar, Iterable, Mapping

from evaluator.shared.context import EvaluationContext
from evaluator.shared.module.result import ModuleResult


class EvaluationModule(ABC):
    """Base class for all config-driven evaluator modules."""

    module_name: ClassVar[str] = "base"

    def __init__(self, name: str, config: Mapping[str, Any]):
        self.name = name
        self.config = dict(config)

    def run(self, context: EvaluationContext) -> ModuleResult:
        started = time.perf_counter()
        try:
            result = self.evaluate(context)
        except Exception as exc:  # pragma: no cover - defensive error shaping
            result = ModuleResult(
                name=self.name,
                module_name=self.module_name,
                passed=False,
                findings=[f"{self.module_name} module crashed: {exc}"],
            )
        duration_ms = int((time.perf_counter() - started) * 1000)
        return ModuleResult(
            name=result.name,
            module_name=result.module_name,
            passed=result.passed,
            findings=result.findings,
            details=result.details,
            duration_ms=duration_ms,
        )

    @abstractmethod
    def evaluate(self, context: EvaluationContext) -> ModuleResult:
        raise NotImplementedError

    def _base_result(
        self,
        *,
        passed: bool,
        findings: Iterable[str],
        details: Mapping[str, Any] | None = None,
    ) -> ModuleResult:
        return ModuleResult(
            name=self.name,
            module_name=self.module_name,
            passed=passed,
            findings=list(findings),
            details=dict(details or {}),
        )

    def _require_baseline(self, context: EvaluationContext) -> Path:
        if context.baseline_case_root is None:
            raise ValueError(
                f"Module '{self.name}' requires baseline_case_root but none was provided"
            )
        return context.baseline_case_root

    def _resolve_root(self, key: str, context: EvaluationContext) -> Path:
        roots = {
            "repo_root": context.repo_root,
            "case_root": context.case_root,
            "baseline_case_root": context.baseline_case_root,
            "evaluator_root": context.evaluator_root,
            "build_dir": context.build_dir,
        }
        root = roots.get(key)
        if root is None:
            raise ValueError(
                f"Context root '{key}' is not available for module '{self.name}'"
            )
        return root

    def _format_string(self, value: str, context: EvaluationContext) -> str:
        return value.format_map(context.format_tokens())

    def _resolve_path_value(
        self,
        value: str | Path,
        *,
        context: EvaluationContext,
        relative_to: Path | None = None,
    ) -> Path:
        if isinstance(value, Path):
            raw = value
        else:
            raw = Path(self._format_string(value, context))
        if raw.is_absolute():
            return raw
        if relative_to is not None:
            return (relative_to / raw).resolve()
        return (context.repo_root / raw).resolve()
