from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Submission:
    student_id: str
    content: str
    is_late: bool = False
