from __future__ import annotations

from src.shift_tracker import ShiftTracker


def build_handover_packet_preview(tracker: ShiftTracker) -> str:
    return (
        f"Preview for shift {tracker.shift_id} is not available yet.\n"
        "Use the saved handover packet for now.\n"
    )
