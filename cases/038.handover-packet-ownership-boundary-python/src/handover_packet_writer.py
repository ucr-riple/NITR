from __future__ import annotations

from pathlib import Path

from src.handover_packet import (
    HandoverPacket,
    HandoverPacketRow,
    HandoverPacketSummary,
    render_packet_text,
)
from src.shift_tracker import ShiftTracker


def save_handover_packet(
    tracker: ShiftTracker, output_path: str | Path
) -> HandoverPacket:
    rows = [
        HandoverPacketRow(index, tote.tote_id, tote.package_count, False)
        for index, tote in enumerate(tracker.completed_totes, start=1)
    ]

    if tracker.current_tote is not None:
        rows.append(
            HandoverPacketRow(
                len(rows) + 1,
                tracker.current_tote.tote_id,
                tracker.current_tote.package_count,
                True,
            )
        )

    packet = HandoverPacket(
        shift_id=tracker.shift_id,
        rows=tuple(rows),
        summary=HandoverPacketSummary(
            tote_count=len(rows),
            package_count=sum(row.package_count for row in rows),
        ),
    )
    Path(output_path).write_text(render_packet_text(packet), encoding="utf-8")
    return packet
