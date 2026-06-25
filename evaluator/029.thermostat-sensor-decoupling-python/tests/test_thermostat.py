#!/usr/bin/env python3

from __future__ import annotations

import argparse
import inspect
import os
import subprocess
import sys
import unittest
from pathlib import Path

ARG_PARSER = argparse.ArgumentParser()
ARG_PARSER.add_argument("--case_root", required=True)
ARGS = ARG_PARSER.parse_args()

CASE_ROOT = Path(ARGS.case_root).resolve()
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.thermostat_controller import Command, ThermostatController


class ThermostatControllerTests(unittest.TestCase):
    def test_returns_configured_target_temperature(self) -> None:
        controller = ThermostatController(22.0)
        self.assertEqual(controller.target_temperature(), 22.0)

    def test_heats_at_or_below_lower_threshold(self) -> None:
        controller = ThermostatController(22.0)
        self.assertEqual(controller.evaluate(20.0), Command.HEATING)
        self.assertEqual(controller.evaluate(19.9), Command.HEATING)

    def test_cools_at_or_above_upper_threshold(self) -> None:
        controller = ThermostatController(22.0)
        self.assertEqual(controller.evaluate(24.0), Command.COOLING)
        self.assertEqual(controller.evaluate(24.1), Command.COOLING)

    def test_idles_inside_threshold_band(self) -> None:
        controller = ThermostatController(22.0)
        self.assertEqual(controller.evaluate(22.0), Command.IDLE)
        self.assertEqual(controller.evaluate(20.1), Command.IDLE)
        self.assertEqual(controller.evaluate(23.9), Command.IDLE)

    def test_no_argument_evaluate_path_exists(self) -> None:
        controller = ThermostatController(22.0)
        signature = inspect.signature(controller.evaluate)
        required_parameters = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
            and parameter.default is inspect.Signature.empty
        ]
        self.assertEqual(
            required_parameters,
            [],
            msg="ThermostatController.evaluate() should support a no-argument call path.",
        )

    def test_application_reads_sensor_temperature_end_to_end(self) -> None:
        app_path = CASE_ROOT / "app" / "main.py"
        env = os.environ.copy()
        env["TMP26_SIMULATOR_TEMP"] = "24.0"
        result = subprocess.run(
            [sys.executable, str(app_path), "22.0"],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), "Cooling")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
