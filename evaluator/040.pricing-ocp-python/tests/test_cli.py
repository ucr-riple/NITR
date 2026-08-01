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
CLI = CASE_ROOT / "app" / "main.py"


def runtime_rules(rule_id: str, percent: float) -> str:
    return json.dumps(
        {
            "rules": [
                {
                    "id": rule_id,
                    "type": "percent",
                    "value": percent,
                    "priority": 10,
                    "group": "COUPON",
                    "disables_member": False,
                    "when": {"coupon": "SPECIAL"},
                }
            ]
        }
    )


class PricingCliTests(unittest.TestCase):
    def run_cli(
        self,
        directory: Path,
        input_path: Path,
        output_path: Path,
        milestone: str,
        *,
        rules_path: Path | None = None,
        env_rules_path: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(CLI),
            "--in",
            str(input_path),
            "--out",
            str(output_path),
            "--milestone",
            milestone,
        ]
        if rules_path is not None:
            command.extend(["--rules", str(rules_path)])
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(CASE_ROOT)
        if env_rules_path is None:
            environment.pop("NITR_RULES", None)
        else:
            environment["NITR_RULES"] = str(env_rules_path)
        return subprocess.run(
            command,
            cwd=directory,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_order(self, path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "subtotal": 100.0,
                    "is_member": False,
                    "items": 0,
                    "coupons": ["SPECIAL"],
                }
            ),
            encoding="utf-8",
        )

    def assert_error(
        self, completed: subprocess.CompletedProcess[str], expected: str
    ) -> None:
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, expected + "\n")
        self.assertEqual(completed.stdout, "")

    def test_successful_json_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            input_path = directory / "order.json"
            output_path = directory / "result.json"
            input_path.write_text(
                json.dumps(
                    {
                        "subtotal": 120.0,
                        "is_member": True,
                        "items": 10,
                        "coupons": [],
                    }
                ),
                encoding="utf-8",
            )

            completed = self.run_cli(
                directory, input_path, output_path, "m1"
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stderr, "")
            self.assertEqual(
                json.loads(output_path.read_text(encoding="utf-8")),
                {
                    "final_price": 88.0,
                    "applied_rules": ["ITEMS_20OFF", "MEMBER_10P"],
                },
            )

    def test_runtime_rule_path_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            input_path = directory / "order.json"
            self.write_order(input_path)
            cwd_rules = directory / "rules.json"
            env_rules = directory / "environment.json"
            argument_rules = directory / "argument.json"
            cwd_rules.write_text(runtime_rules("CWD_10P", 0.10), encoding="utf-8")
            env_rules.write_text(runtime_rules("ENV_20P", 0.20), encoding="utf-8")
            argument_rules.write_text(
                runtime_rules("ARG_30P", 0.30), encoding="utf-8"
            )

            scenarios = [
                (argument_rules, env_rules, "ARG_30P", 70.0),
                (None, env_rules, "ENV_20P", 80.0),
                (None, None, "CWD_10P", 90.0),
            ]
            for index, (argument, environment, rule_id, price) in enumerate(
                scenarios
            ):
                with self.subTest(rule_id=rule_id):
                    output_path = directory / f"result-{index}.json"
                    completed = self.run_cli(
                        directory,
                        input_path,
                        output_path,
                        "m4",
                        rules_path=argument,
                        env_rules_path=environment,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    result = json.loads(output_path.read_text(encoding="utf-8"))
                    self.assertEqual(result["final_price"], price)
                    self.assertEqual(result["applied_rules"], [rule_id])

    def test_invalid_json_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            output_path = directory / "result.json"
            invalid_json = directory / "invalid-json.json"
            invalid_json.write_text("{", encoding="utf-8")
            self.assert_error(
                self.run_cli(directory, invalid_json, output_path, "m1"),
                "ERR_INVALID_JSON",
            )

    def test_invalid_input_schema_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            output_path = directory / "result.json"
            invalid_schema = directory / "invalid-schema.json"
            invalid_schema.write_text(
                json.dumps(
                    {
                        "subtotal": "100",
                        "is_member": False,
                        "items": 0,
                        "coupons": [],
                    }
                ),
                encoding="utf-8",
            )
            self.assert_error(
                self.run_cli(directory, invalid_schema, output_path, "m1"),
                "ERR_INVALID_SCHEMA",
            )

    def test_unsupported_milestone_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            output_path = directory / "result.json"
            valid_input = directory / "valid.json"
            self.write_order(valid_input)
            self.assert_error(
                self.run_cli(directory, valid_input, output_path, "m5"),
                "ERR_UNSUPPORTED_MILESTONE",
            )

    def test_io_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            output_path = directory / "result.json"
            missing_input = directory / "missing.json"
            self.assert_error(
                self.run_cli(directory, missing_input, output_path, "m1"),
                "ERR_IO",
            )

    def test_invalid_runtime_rules_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            output_path = directory / "result.json"
            valid_input = directory / "valid.json"
            self.write_order(valid_input)
            invalid_rules = directory / "invalid-rules.json"
            invalid_rules.write_text(
                '{"rules":[{"id":"BAD","type":"percent","value":1.5}]}',
                encoding="utf-8",
            )
            self.assert_error(
                self.run_cli(
                    directory,
                    valid_input,
                    output_path,
                    "m4",
                    rules_path=invalid_rules,
                ),
                "ERR_INVALID_SCHEMA",
            )

            invalid_rules.write_text("{", encoding="utf-8")
            self.assert_error(
                self.run_cli(
                    directory,
                    valid_input,
                    output_path,
                    "m4",
                    rules_path=invalid_rules,
                ),
                "ERR_INVALID_SCHEMA",
            )


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
