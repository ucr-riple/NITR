#!/usr/bin/env python3

"""Evaluation module package and aggregation entrypoint."""

from __future__ import annotations

from typing import Any, Mapping

from evaluator.shared.module.base import EvaluationModule
from evaluator.shared.module.baseline_diff_module import BaselineDiffModule
from evaluator.shared.module.build_module import BuildModule
from evaluator.shared.module.customized_check_module import CustomizedCheckModule
from evaluator.shared.module.frozen_paths_module import FrozenPathsModule
from evaluator.shared.module.required_paths_module import RequiredPathsModule
from evaluator.shared.module.result import ModuleResult
from evaluator.shared.module.source_analysis_module import SourceAnalysisModule
from evaluator.shared.module.unit_test_module import UnitTestModule

MODULE_REGISTRY: dict[str, type[EvaluationModule]] = {
    BuildModule.module_name: BuildModule,
    CustomizedCheckModule.module_name: CustomizedCheckModule,
    UnitTestModule.module_name: UnitTestModule,
    RequiredPathsModule.module_name: RequiredPathsModule,
    BaselineDiffModule.module_name: BaselineDiffModule,
    FrozenPathsModule.module_name: FrozenPathsModule,
    SourceAnalysisModule.module_name: SourceAnalysisModule,
}


def module_from_config(config: Mapping[str, Any]) -> EvaluationModule:
    module_name = config.get("module_name")
    if not module_name:
        raise ValueError("Each module config requires a 'module_name'")
    instance_name = config.get("name", module_name)
    module_class = MODULE_REGISTRY.get(module_name)
    if module_class is None:
        raise ValueError(f"Unsupported module_name: {module_name}")
    return module_class(name=instance_name, config=config)


__all__ = [
    "BaselineDiffModule",
    "BuildModule",
    "CustomizedCheckModule",
    "EvaluationModule",
    "FrozenPathsModule",
    "MODULE_REGISTRY",
    "ModuleResult",
    "RequiredPathsModule",
    "SourceAnalysisModule",
    "UnitTestModule",
    "module_from_config",
]
