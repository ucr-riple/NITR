from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EventKind(Enum):
    SAMPLE = "sample"
    ACQUIRE = "acquire"
    RELEASE = "release"


@dataclass(frozen=True)
class Event:
    channel: str
    kind: EventKind = EventKind.SAMPLE
    value: float = 0.0


@dataclass(frozen=True)
class Config:
    low_bound: float = 0.0
    high_bound: float = 0.0
    drift_tolerance: float = 0.0


@dataclass(frozen=True)
class RangeAlert:
    channel: str
    value: float


@dataclass(frozen=True)
class DriftAlert:
    channel: str
    value: float
    baseline: float


@dataclass(frozen=True)
class LeakAlert:
    channel: str


@dataclass
class Report:
    range_alerts: list[RangeAlert] = field(default_factory=list)
    drift_alerts: list[DriftAlert] = field(default_factory=list)
    leak_alerts: list[LeakAlert] = field(default_factory=list)


def analyze(events: list[Event], config: Config) -> Report:
    report = Report()
    for event in events:
        if event.kind is not EventKind.SAMPLE:
            continue
        if event.value < config.low_bound or event.value > config.high_bound:
            report.range_alerts.append(RangeAlert(event.channel, event.value))
    return report
