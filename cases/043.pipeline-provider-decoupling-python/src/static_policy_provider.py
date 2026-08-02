from __future__ import annotations
from src.models import Policy
from src.policy_provider import PolicyProvider

class StaticPolicyProvider(PolicyProvider):
    def __init__(self) -> None:
        self._policies = {"web": Policy("silver", 45), "mobile": Policy("gold", 90), "partner": Policy("archive", 180)}

    def lookup(self, source_id: str) -> Policy:
        return self._policies.get(source_id, Policy.fallback())
