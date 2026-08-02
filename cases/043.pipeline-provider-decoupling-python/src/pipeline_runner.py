from __future__ import annotations
from collections.abc import Sequence
from src.models import Event
from src.policy_provider import PolicyProvider

class PipelineRunner:
    def __init__(self, enable_policy_enrichment: bool, policy_provider: PolicyProvider | None) -> None:
        self._enable_policy_enrichment = enable_policy_enrichment
        self._policy_provider = policy_provider

    def run(self, events: Sequence[Event]) -> list[str]:
        output = []
        for event in events:
            line = f"source={event.source_id};payload={event.payload.upper().replace(' ', '_')};score={event.score}"
            output.append(line)
        return output
