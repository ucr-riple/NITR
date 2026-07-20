from __future__ import annotations

from pathlib import Path

from src.handover_packet_preview import build_handover_packet_preview
from src.handover_packet_writer import save_handover_packet
from src.shift_tracker import ShiftTracker


def main() -> None:
    tracker = ShiftTracker("SHIFT-042")
    tracker.add_completed_tote("TOTE-100", 4)
    tracker.add_completed_tote("TOTE-101", 3)
    tracker.start_tote("TOTE-102")
    tracker.scan_packages_into_current_tote(2)

    output_path = Path("handover_packet.txt")
    print(build_handover_packet_preview(tracker), end="")

    packet = save_handover_packet(tracker, output_path)
    print(f"Saved {len(packet.rows)} packet rows to {output_path}")


if __name__ == "__main__":
    main()
