from __future__ import annotations

from src.applicant import Applicant
from src.audit_logger import NullAuditLogger
from src.loan_review_service import review_applicants


def main() -> None:
    applicants = [
        Applicant("alice", 750, 90000, 0.20),
        Applicant("bob", 650, 80000, 0.30),
    ]
    result = review_applicants(applicants, NullAuditLogger())
    print(f"approved={len(result.approved_ids)}")


if __name__ == "__main__":
    main()
