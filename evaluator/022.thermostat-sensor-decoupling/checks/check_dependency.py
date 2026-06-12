#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from evaluator.shared.check_utils import (
    case_root_from_script,
    include_paths,
    read_text,
    strip_comments_and_strings,
)


def has_any_pattern(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", type=Path, default=case_root_from_script(__file__))
    args = parser.parse_args()

    case_root = args.case_root.resolve()

    src_root = case_root / "src"
    sensor_source_path = src_root / "tmp26_sensor.cc"
    app_main_path = case_root / "app" / "main.cc"

    core_files = sorted(
        path
        for path in src_root.rglob("*")
        if path.suffix in {".h", ".cc"}
        and path.name not in {"tmp26_sensor.h", "tmp26_sensor.cc", "main.cc"}
    )

    core_text_by_file: dict[Path, str] = {path: read_text(path) for path in core_files}
    sensor_source_text = read_text(sensor_source_path)
    app_main_text = read_text(app_main_path)

    if not core_files or any(not text for text in core_text_by_file.values()):
        print(
            "Structural check failed: could not read all core source files under "
            f"{src_root}."
        )
        return 1
    if not app_main_text:
        print(
            "Structural check failed: could not read app entrypoint at "
            f"{app_main_path}."
        )
        return 1

    failures: list[str] = []
    forbidden_core_coupling_patterns = [
        r"\bTmp26Sensor\b",
        r"\bgetenv\s*\(",
        r"\bTMP26_SIMULATOR_TEMP\b",
    ]

    for path, raw_text in core_text_by_file.items():
        scanned_text = strip_comments_and_strings(raw_text)
        includes = include_paths(raw_text)

        if any(include.endswith("tmp26_sensor.h") for include in includes):
            failures.append(
                f"{path.name}: core thermostat logic must not include hardware sensor "
                "headers directly."
            )

        if any(include.startswith("src/") for include in includes):
            failures.append(
                f'{path.name}: do not use #include "src/..."; keep starter relative '
                "include style."
            )

        if has_any_pattern(forbidden_core_coupling_patterns, scanned_text):
            failures.append(
                f"{path.name}: core thermostat logic must not reference hardware "
                "sensor or environment-specific reading hooks directly."
            )

    if 'std::getenv("TMP26_SIMULATOR_TEMP")' not in sensor_source_text:
        failures.append(
            "src/tmp26_sensor.cc must keep the starter simulator backdoor behavior."
        )

    scanned_main_text = strip_comments_and_strings(app_main_text)
    has_no_arg_evaluate_call = re.search(r"\.\s*Evaluate\s*\(\s*\)", scanned_main_text)
    has_arg_evaluate_call = re.search(r"\.\s*Evaluate\s*\(\s*[^)\s]", scanned_main_text)

    if not has_no_arg_evaluate_call:
        failures.append(
            "app/main.cc must call ThermostatController::Evaluate() without "
            "passing current temperature manually."
        )

    if has_arg_evaluate_call:
        failures.append(
            "app/main.cc should not call ThermostatController::Evaluate(...) "
            "with manual temperature arguments."
        )

    if failures:
        print("Maintainability check failed:")
        for failure in failures:
            print(f"- {failure}")
        print(
            "ThermostatController should keep policy logic free of hardware and "
            "environment-specific reading details. Wire concrete sensor access "
            "outside the core controller files."
        )
        return 1

    print("Dependency check passed: ThermostatController remains decoupled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
