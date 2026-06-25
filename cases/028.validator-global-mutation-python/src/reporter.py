from __future__ import annotations

import src.stats as stats


class Reporter:
    def summary(self) -> str:
        return f"Processed {stats.total_processed} submissions"
