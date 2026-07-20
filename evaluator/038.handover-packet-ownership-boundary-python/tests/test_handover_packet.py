#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import tempfile
import unittest
from pathlib import Path

ARG_PARSER = argparse.ArgumentParser()
ARG_PARSER.add_argument("--case_root", required=True)
ARGS = ARG_PARSER.parse_args()

CASE_ROOT = Path(ARGS.case_root).resolve()
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.handover_packet_preview import build_handover_packet_preview
from src.handover_packet_writer import save_handover_packet
from src.shift_tracker import ShiftTracker

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
EXPECTED_IN_PROGRESS = (DATA_ROOT / "expected_packet_with_in_progress.txt").read_text(
    encoding="utf-8"
)
EXPECTED_CLOSED = (DATA_ROOT / "expected_packet_without_in_progress.txt").read_text(
    encoding="utf-8"
)


def build_in_progress_tracker() -> ShiftTracker:
    tracker = ShiftTracker("SHIFT-500")
    tracker.add_completed_tote("TOTE-100", 4)
    tracker.add_completed_tote("TOTE-101", 3)
    tracker.start_tote("TOTE-102")
    tracker.scan_packages_into_current_tote(2)
    return tracker


def build_closed_tracker() -> ShiftTracker:
    tracker = ShiftTracker("SHIFT-501")
    tracker.add_completed_tote("TOTE-200", 5)
    tracker.add_completed_tote("TOTE-201", 1)
    tracker.start_tote("TOTE-202")
    tracker.scan_packages_into_current_tote(2)
    tracker.close_current_tote()
    return tracker


class HandoverPacketTests(unittest.TestCase):
    def save(self, tracker: ShiftTracker) -> tuple[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "packet.txt"
            packet = save_handover_packet(tracker, output_path)
            return output_path.read_text(encoding="utf-8"), packet

    def test_preview_and_save_with_in_progress_tote(self) -> None:
        tracker = build_in_progress_tracker()

        preview = build_handover_packet_preview(tracker)
        saved, packet = self.save(tracker)

        self.assertEqual(preview, EXPECTED_IN_PROGRESS)
        self.assertEqual(saved, EXPECTED_IN_PROGRESS)
        self.assertEqual(packet.rows[-1].tote_id, "TOTE-102")
        self.assertTrue(packet.rows[-1].from_in_progress_tote)
        self.assertEqual(packet.summary.tote_count, 3)
        self.assertEqual(packet.summary.package_count, 9)

    def test_preview_and_save_without_in_progress_tote(self) -> None:
        tracker = build_closed_tracker()

        preview = build_handover_packet_preview(tracker)
        saved, packet = self.save(tracker)

        self.assertEqual(preview, EXPECTED_CLOSED)
        self.assertEqual(saved, EXPECTED_CLOSED)
        self.assertFalse(packet.rows[-1].from_in_progress_tote)
        self.assertEqual(packet.summary.tote_count, 3)
        self.assertEqual(packet.summary.package_count, 8)

    def test_preview_then_save_is_stable(self) -> None:
        tracker = build_in_progress_tracker()

        first_preview = build_handover_packet_preview(tracker)
        first_saved, first_packet = self.save(tracker)
        second_preview = build_handover_packet_preview(tracker)
        second_saved, second_packet = self.save(tracker)

        self.assertEqual(first_preview, second_preview)
        self.assertEqual(first_saved, second_saved)
        self.assertEqual(first_packet, second_packet)

    def test_save_then_preview_is_stable(self) -> None:
        tracker = build_in_progress_tracker()

        saved, packet = self.save(tracker)
        preview = build_handover_packet_preview(tracker)

        self.assertEqual(saved, preview)
        self.assertEqual(packet.rows[-1].package_count, 2)
        self.assertEqual(tracker.current_tote.package_count, 2)

    def test_row_numbers_are_sequential(self) -> None:
        tracker = build_in_progress_tracker()

        _, packet = self.save(tracker)

        self.assertEqual([row.row_number for row in packet.rows], [1, 2, 3])


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
