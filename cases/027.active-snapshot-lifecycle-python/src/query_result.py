from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class QueryStatus(str, Enum):
    FOUND = "kFound"
    NOT_FOUND = "kNotFound"
    NO_ACTIVE_SNAPSHOT = "kNoActiveSnapshot"


@dataclass(frozen=True)
class QueryResult:
    status: QueryStatus
    value: str
    served_version: str
