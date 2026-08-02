from __future__ import annotations
import json
from pathlib import Path
from src.models import Policy
from src.policy_provider import PolicyProvider

class FilePolicyProvider(PolicyProvider):
    def __init__(self, policy_file_path: str) -> None:
        try:
            raw = json.loads(Path(policy_file_path).read_text(encoding="utf-8"))
            self._policies = {key: Policy(value["policy_tier"], value["retention_days"]) for key, value in raw.items()}
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            self._policies = {}

    def lookup(self, source_id: str) -> Policy:
        return self._policies.get(source_id, Policy.fallback())
