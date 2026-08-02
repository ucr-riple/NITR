from __future__ import annotations
from abc import ABC, abstractmethod
from src.models import Policy

class PolicyProvider(ABC):
    @abstractmethod
    def lookup(self, source_id: str) -> Policy:
        """Return policy for a source or the fallback policy."""
