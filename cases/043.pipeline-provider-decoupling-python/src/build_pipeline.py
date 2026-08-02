from __future__ import annotations
from dataclasses import dataclass
from src.models import PipelineConfig
from src.pipeline_runner import PipelineRunner
from src.policy_provider import PolicyProvider

@dataclass
class BuiltPipeline:
    policy_provider: PolicyProvider | None
    runner: PipelineRunner

def build_pipeline(config: PipelineConfig) -> BuiltPipeline:
    return BuiltPipeline(None, PipelineRunner(config.enable_policy_enrichment, None))
