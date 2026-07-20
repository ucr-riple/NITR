from __future__ import annotations

from abc import ABC, abstractmethod

from src.report import Report


class ReportExporter(ABC):
    @abstractmethod
    def can_handle(self, format_key: str) -> bool:
        """Return whether this exporter supports the requested format."""

    @abstractmethod
    def export(self, report: Report) -> str:
        """Render the report."""
