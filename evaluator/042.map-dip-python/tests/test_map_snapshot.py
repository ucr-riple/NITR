#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
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

from src.map_snapshot import (
    GLOBAL_LAYER_REGISTRY,
    LayerProvider,
    MapSnapshotService,
)


class ReversePayloadProvider(LayerProvider):
    @property
    def name(self) -> str:
        return "reverse_payload"

    def build_layer(self, payload: str) -> str:
        return payload[::-1]


class PrefixProvider(LayerProvider):
    def __init__(self, prefix: str) -> None:
        self._prefix = prefix

    @property
    def name(self) -> str:
        return "prefix"

    def build_layer(self, payload: str) -> str:
        return self._prefix + payload


class MapSnapshotTests(unittest.TestCase):
    def test_builtin_layers_preserve_snapshot_format(self) -> None:
        config = {"layers": [{"type": "geometry"}, {"type": "semantics"}]}
        self.assertEqual(
            MapSnapshotService().build_snapshot(config, "  foo bar42  \n"),
            "SNAPSHOT\ngeometry:alnum_count=8\nsemantics:first_token=foo\n",
        )

    def test_evaluator_plugin_extends_without_core_changes(self) -> None:
        GLOBAL_LAYER_REGISTRY.register(
            "reverse_payload", lambda _: ReversePayloadProvider()
        )
        config = {"layers": [{"type": "reverse_payload"}]}
        self.assertEqual(
            MapSnapshotService().build_snapshot(config, "abcd"),
            "SNAPSHOT\nreverse_payload:dcba\n",
        )

    def test_creator_receives_layer_configuration(self) -> None:
        GLOBAL_LAYER_REGISTRY.register(
            "prefix", lambda config: PrefixProvider(config["prefix"])
        )
        config = {"layers": [{"type": "prefix", "prefix": "map:"}]}
        self.assertEqual(
            MapSnapshotService().build_snapshot(config, "road"),
            "SNAPSHOT\nprefix:map:road\n",
        )

    def test_unknown_and_invalid_layers_fail(self) -> None:
        service = MapSnapshotService()
        with self.assertRaisesRegex(ValueError, "layers"):
            service.build_snapshot({}, "")
        with self.assertRaisesRegex(ValueError, "unknown layer type"):
            service.build_snapshot({"layers": [{"type": "missing"}]}, "")

    def test_cli_reads_config_and_all_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            config_path = directory / "config.json"
            config_path.write_text(
                json.dumps({"layers": [{"type": "geometry"}, {"type": "semantics"}]}),
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(CASE_ROOT)
            completed = subprocess.run(
                [sys.executable, str(CASE_ROOT / "app" / "main.py"), str(config_path)],
                input="  foo bar42  \n",
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                completed.stdout,
                "SNAPSHOT\ngeometry:alnum_count=8\nsemantics:first_token=foo\n",
            )


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
