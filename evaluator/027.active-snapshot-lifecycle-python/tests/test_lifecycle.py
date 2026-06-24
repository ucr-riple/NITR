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

from src.query_result import QueryStatus
from src.query_service import QueryService
from src.snapshot_store import SnapshotStore


class LifecycleTests(unittest.TestCase):
    def test_baseline_active_query_behavior(self) -> None:
        store = SnapshotStore()
        query = QueryService(store)

        payload = {"k": "one", "x": "1"}
        self.assertTrue(store.register_snapshot("v1", payload))
        self.assertTrue(store.activate_snapshot("v1"))

        result = query.lookup("k")
        self.assertEqual(result.status, QueryStatus.FOUND)
        self.assertEqual(result.value, "one")
        self.assertEqual(result.served_version, "v1")

    def test_activate_replace_behavior(self) -> None:
        store = SnapshotStore()
        query = QueryService(store)

        self.assertTrue(store.register_snapshot("v1", {"name": "alpha"}))
        self.assertTrue(store.register_snapshot("v2", {"name": "beta"}))
        self.assertTrue(store.activate_snapshot("v1"))
        self.assertEqual(query.lookup("name").value, "alpha")

        self.assertTrue(store.activate_snapshot("v2"))
        result = query.lookup("name")
        self.assertEqual(result.status, QueryStatus.FOUND)
        self.assertEqual(result.value, "beta")
        self.assertEqual(result.served_version, "v2")

    def test_reset_and_no_active_behavior(self) -> None:
        store = SnapshotStore()
        query = QueryService(store)

        self.assertTrue(store.register_snapshot("v1", {"color": "blue"}))
        self.assertTrue(store.activate_snapshot("v1"))
        self.assertEqual(query.lookup("color").status, QueryStatus.FOUND)

        store.reset_active_snapshot()
        result = query.lookup("color")
        self.assertEqual(result.status, QueryStatus.NO_ACTIVE_SNAPSHOT)
        self.assertEqual(result.value, "")

        store.reset_active_snapshot()
        result = query.lookup("color")
        self.assertEqual(result.status, QueryStatus.NO_ACTIVE_SNAPSHOT)

    def test_unknown_activation_does_not_replace_active(self) -> None:
        store = SnapshotStore()
        query = QueryService(store)

        self.assertTrue(store.register_snapshot("v1", {"city": "rome"}))
        self.assertTrue(store.activate_snapshot("v1"))
        self.assertFalse(store.activate_snapshot("missing-version"))

        result = query.lookup("city")
        self.assertEqual(result.status, QueryStatus.FOUND)
        self.assertEqual(result.value, "rome")
        self.assertEqual(result.served_version, "v1")

    def test_duplicate_registration_rejected(self) -> None:
        store = SnapshotStore()
        query = QueryService(store)

        self.assertTrue(store.register_snapshot("v1", {"id": "first"}))
        self.assertFalse(store.register_snapshot("v1", {"id": "second"}))

        self.assertTrue(store.activate_snapshot("v1"))
        result = query.lookup("id")
        self.assertEqual(result.status, QueryStatus.FOUND)
        self.assertEqual(result.value, "first")

    def test_repeated_transitions_and_isolation(self) -> None:
        store = SnapshotStore()
        query = QueryService(store)

        self.assertTrue(store.register_snapshot("v1", {"shared": "A"}))
        self.assertTrue(store.register_snapshot("v2", {"shared": "B"}))
        self.assertTrue(store.register_snapshot("v3", {"shared": "C"}))

        self.assertTrue(store.activate_snapshot("v1"))
        self.assertEqual(query.lookup("shared").value, "A")

        self.assertTrue(store.activate_snapshot("v2"))
        self.assertEqual(query.lookup("shared").value, "B")

        self.assertTrue(store.activate_snapshot("v3"))
        self.assertEqual(query.lookup("shared").value, "C")

        store.reset_active_snapshot()
        result = query.lookup("shared")
        self.assertEqual(result.status, QueryStatus.NO_ACTIVE_SNAPSHOT)

        self.assertTrue(store.activate_snapshot("v2"))
        result = query.lookup("shared")
        self.assertEqual(result.status, QueryStatus.FOUND)
        self.assertEqual(result.value, "B")

    def test_registration_copies_payload_ownership(self) -> None:
        store = SnapshotStore()
        query = QueryService(store)

        payload = {"mode": "draft"}
        self.assertTrue(store.register_snapshot("v1", payload))
        payload["mode"] = "mutated"

        self.assertTrue(store.activate_snapshot("v1"))
        result = query.lookup("mode")
        self.assertEqual(result.status, QueryStatus.FOUND)
        self.assertEqual(result.value, "draft")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
