from __future__ import annotations

from src.monitor import Config, Event, EventKind, analyze


def main() -> None:
    events = [
        Event("temp", EventKind.SAMPLE, 20.0),
        Event("temp", EventKind.SAMPLE, 80.0),
        Event("valve", EventKind.ACQUIRE, 0.0),
        Event("temp", EventKind.SAMPLE, 21.0),
    ]
    config = Config(0.0, 50.0, 5.0)
    report = analyze(events, config)
    print(
        f"range={len(report.range_alerts)} "
        f"drift={len(report.drift_alerts)} "
        f"leak={len(report.leak_alerts)}"
    )


if __name__ == "__main__":
    main()
