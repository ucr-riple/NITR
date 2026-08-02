from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Event:
    source_id: str
    payload: str
    score: int = 0

@dataclass(frozen=True)
class Policy:
    policy_tier: str
    retention_days: int = 30

    @staticmethod
    def fallback() -> "Policy":
        return Policy("standard", 30)

@dataclass(frozen=True)
class PipelineConfig:
    policy_mode: str = "static"
    policy_file_path: str = ""
    enable_policy_enrichment: bool = False
