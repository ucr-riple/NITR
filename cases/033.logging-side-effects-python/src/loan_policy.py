from __future__ import annotations

from dataclasses import dataclass, field

from src.applicant import Applicant


@dataclass(frozen=True)
class ReviewDecision:
    approved: bool = False
    denial_reasons: list[str] = field(default_factory=list)


def evaluate_applicant(applicant: Applicant) -> ReviewDecision:
    del applicant
    return ReviewDecision()
