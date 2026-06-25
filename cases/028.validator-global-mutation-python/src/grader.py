from __future__ import annotations

from src.submission import Submission


class Grader:
    def grade(self, submission: Submission) -> int:
        return min(len(submission.content), 100)
