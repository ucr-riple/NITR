from __future__ import annotations

import time
from abc import ABC, abstractmethod


class TimeSource(ABC):
    @abstractmethod
    def now_seconds(self) -> int:
        raise NotImplementedError


class SystemTimeSource(TimeSource):
    def now_seconds(self) -> int:
        return int(time.time())
