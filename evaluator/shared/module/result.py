#!/usr/bin/env python3

"""Evaluation module result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModuleResult:
    name: str
    module_name: str
    passed: bool
    findings: list[str]
    details: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "module_name": self.module_name,
            "passed": self.passed,
            "findings": self.findings,
            "duration_ms": self.duration_ms,
        }
        if self.details:
            payload["details"] = self.details
        return payload
