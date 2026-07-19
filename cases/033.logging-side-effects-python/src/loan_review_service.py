from __future__ import annotations

from dataclasses import dataclass, field

from src.applicant import Applicant
from src.audit_logger import AuditLogger
from src.loan_policy import evaluate_applicant


@dataclass
class ReviewBatchResult:
    approved_ids: list[str] = field(default_factory=list)


def review_applicants(
    applicants: list[Applicant], logger: AuditLogger | None
) -> ReviewBatchResult:
    result = ReviewBatchResult()
    for applicant in applicants:
        decision = evaluate_applicant(applicant)
        if logger is not None:
            logger.log("pending")
        if decision.approved:
            result.approved_ids.append(applicant.id)
    return result
