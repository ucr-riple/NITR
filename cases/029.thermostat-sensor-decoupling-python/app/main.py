#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parents[1]
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.thermostat_controller import Command, ThermostatController
from src.tmp26_sensor import Tmp26Sensor


def command_to_string(command: Command) -> str:
    if command is Command.HEATING:
        return "Heating"
    if command is Command.COOLING:
        return "Cooling"
    return "Idle"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(f"Usage: {argv[0]} <target_temperature>", file=sys.stderr)
        return 1

    target = float(argv[1])
    controller = ThermostatController(target)

    sensor = Tmp26Sensor()
    current_temp = sensor.read_temperature()
    command = controller.evaluate(current_temp)

    print(command_to_string(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
