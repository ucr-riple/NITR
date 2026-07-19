from __future__ import annotations

from abc import ABC, abstractmethod


class AuditLogger(ABC):
    @abstractmethod
    def log(self, message: str) -> None:
        """Record one audit message."""


class NullAuditLogger(AuditLogger):
    def log(self, message: str) -> None:
        del message
