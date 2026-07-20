from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HandoverPacketRow:
    row_number: int
    tote_id: str
    package_count: int
    from_in_progress_tote: bool


@dataclass(frozen=True)
class HandoverPacketSummary:
    tote_count: int
    package_count: int


@dataclass(frozen=True)
class HandoverPacket:
    shift_id: str
    rows: tuple[HandoverPacketRow, ...]
    summary: HandoverPacketSummary


def render_packet_text(packet: HandoverPacket) -> str:
    output = f"Handover packet for shift {packet.shift_id}\nRows:\n"
    for row in packet.rows:
        output += f"  {row.row_number}. {row.tote_id} packages={row.package_count}"
        if row.from_in_progress_tote:
            output += " [in-progress]"
        output += "\n"
    output += (
        f"Summary: totes={packet.summary.tote_count}, "
        f"packages={packet.summary.package_count}\n"
    )
    return output
