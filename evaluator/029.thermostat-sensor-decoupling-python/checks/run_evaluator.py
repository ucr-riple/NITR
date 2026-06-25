#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root)
    src_dir = case_root / "src"
    controller_path = src_dir / "thermostat_controller.py"
    sensor_path = src_dir / "tmp26_sensor.py"
    app_main = case_root / "app" / "main.py"

    required_paths = [
        controller_path,
        sensor_path,
        app_main,
    ]

    findings: list[str] = []
    for path in required_paths:
        if not path.is_file():
            findings.append(f"missing required path: {path.relative_to(case_root)}")

    if controller_path.is_file():
        controller_text = read_text(controller_path)
        if re.search(r"\bTmp26Sensor\b", controller_text):
            findings.append(
                "thermostat_controller.py: core thermostat logic must not reference the concrete hardware sensor directly."
            )
        if re.search(r"\bgetenv\s*\(|\bos\.getenv\s*\(", controller_text):
            findings.append(
                "thermostat_controller.py: core thermostat logic must not read environment-specific sensor state directly."
            )
        if re.search(r"\bTMP26_SIMULATOR_TEMP\b", controller_text):
            findings.append(
                "thermostat_controller.py: core thermostat logic must not reference TMP26_SIMULATOR_TEMP directly."
            )
        if re.search(
            r"^\s*(?:import\s+.*tmp26_sensor\b|from\s+.*tmp26_sensor\s+import\b)",
            controller_text,
            re.MULTILINE,
        ):
            findings.append(
                "thermostat_controller.py: core thermostat logic must not import tmp26_sensor directly."
            )

    if sensor_path.is_file():
        sensor_text = read_text(sensor_path)
        if (
            'os.getenv("TMP26_SIMULATOR_TEMP")' not in sensor_text
            and "os.getenv('TMP26_SIMULATOR_TEMP')" not in sensor_text
        ):
            findings.append(
                "tmp26_sensor.py must keep the TMP26_SIMULATOR_TEMP simulator behavior."
            )

    if app_main.is_file():
        main_text = read_text(app_main)
        if not re.search(r"\.evaluate\s*\(\s*\)", main_text):
            findings.append(
                "app/main.py must call ThermostatController.evaluate() without passing current temperature manually."
            )
        if re.search(r"\.evaluate\s*\(\s*[^)\s]", main_text):
            findings.append(
                "app/main.py should not call ThermostatController.evaluate(...) with manual temperature arguments."
            )

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: structural checks succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
