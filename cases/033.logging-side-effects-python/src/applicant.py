from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Applicant:
    id: str
    credit_score: int = 0
    annual_income: int = 0
    debt_ratio: float = 0.0
