#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

ARG_PARSER = argparse.ArgumentParser()
ARG_PARSER.add_argument("--case_root", required=True)
ARGS = ARG_PARSER.parse_args()

CASE_ROOT = Path(ARGS.case_root).resolve()
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.session_manager import SessionManager
from src.time_source import TimeSource


class ManualTimeSource(TimeSource):
    def __init__(self, now_seconds: int) -> None:
        self._now_seconds = now_seconds

    def now_seconds(self) -> int:
        return self._now_seconds

    def advance_seconds(self, delta_seconds: int) -> None:
        self._now_seconds += delta_seconds


class SessionManagerTests(unittest.TestCase):
    def test_created_session_is_immediately_valid(self) -> None:
        clock = ManualTimeSource(100)
        manager = SessionManager(10, time_source=clock)

        self.assertTrue(manager.create_session("s1"))
        self.assertTrue(manager.is_valid("s1"))

    def test_expires_at_boundary(self) -> None:
        clock = ManualTimeSource(100)
        manager = SessionManager(10, time_source=clock)

        self.assertTrue(manager.create_session("s1"))
        clock.advance_seconds(9)
        self.assertTrue(manager.is_valid("s1"))

        clock.advance_seconds(1)
        self.assertFalse(manager.is_valid("s1"))

    def test_refresh_restarts_window(self) -> None:
        clock = ManualTimeSource(100)
        manager = SessionManager(10, time_source=clock)

        self.assertTrue(manager.create_session("s1"))
        clock.advance_seconds(5)
        self.assertTrue(manager.refresh_session("s1"))

        clock.advance_seconds(9)
        self.assertTrue(manager.is_valid("s1"))

        clock.advance_seconds(1)
        self.assertFalse(manager.is_valid("s1"))

    def test_cannot_refresh_expired_session(self) -> None:
        clock = ManualTimeSource(100)
        manager = SessionManager(10, time_source=clock)

        self.assertTrue(manager.create_session("s1"))
        clock.advance_seconds(10)
        self.assertFalse(manager.refresh_session("s1"))

    def test_remove_invalidates_session(self) -> None:
        clock = ManualTimeSource(100)
        manager = SessionManager(10, time_source=clock)

        self.assertTrue(manager.create_session("s1"))
        self.assertTrue(manager.remove_session("s1"))
        self.assertFalse(manager.is_valid("s1"))


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
