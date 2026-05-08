#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def strip_comments_and_strings(text: str) -> str:
    # Remove block comments first so nested // inside them does not matter.
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    # Remove string and char literals to avoid false positives on messages.
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    text = re.sub(r"'(?:\\.|[^'\\])+'", "''", text)
    return text


def include_paths(text: str) -> list[str]:
    includes: list[str] = []
    for line in text.splitlines():
        match = re.match(r'^\s*#\s*include\s*[<"]([^">]+)[">]', line)
        if match:
            includes.append(match.group(1))
    return includes


def main() -> int:
    if len(sys.argv) > 1:
        case_root = Path(sys.argv[1]).resolve()
    else:
        repo_root = Path(__file__).resolve().parents[3]
        case_root = repo_root / "cases" / "022.thermostat-sensor-decoupling"

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

        if re.search(r"\bTmp26Sensor\b", scanned_text):
            failures.append(
                f"{path.name}: core thermostat logic must not reference a "
                "hardware sensor types directly."
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
            "ThermostatController should depend on an abstract temperature source, "
            "not a concrete hardware implementation."
        )
        return 1

    print("Dependency check passed: ThermostatController remains decoupled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
