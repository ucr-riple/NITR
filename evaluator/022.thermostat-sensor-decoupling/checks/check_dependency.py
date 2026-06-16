#!/usr/bin/env python3

"""Enforce thermostat decoupling boundary for case 022.

Rule:
  - Core thermostat/domain files must not include sensor hardware headers or
    hardware-only symbols directly.
  - App entrypoint must keep temperature acquisition via `Evaluate()` no-arg
    contract.

Inputs:
  - `--case_root` (defaults to script's case root).
  - Core `src/*.h|*.cc` excluding sensor implementation files.
  - `src/tmp26_sensor.cc` and `app/main.cc`.

Output:
  - emit_check_result(passed=<bool>, findings=[violation messages]).
"""

import argparse
from pathlib import Path

from evaluator.shared.module.path_checks import (
    case_root_from_script,
    read_text,
    scan_files,
)
from evaluator.shared.check_output import emit_check_result
from evaluator.shared.module.source_analysis import (
    has_any_pattern,
    include_paths,
    strip_comments_and_strings,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root", type=Path, default=case_root_from_script(__file__)
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()

    src_root = case_root / "src"
    sensor_source_path = src_root / "tmp26_sensor.cc"
    app_main_path = case_root / "app" / "main.cc"

    core_files = [
        path
        for path in scan_files(src_root, suffixes=(".h", ".cc"))
        if path.name not in {"tmp26_sensor.h", "tmp26_sensor.cc", "main.cc"}
    ]

    core_text_by_file: dict[Path, str] = {path: read_text(path) for path in core_files}
    sensor_source_text = read_text(sensor_source_path)
    app_main_text = read_text(app_main_path)

    if not core_files or any(not text for text in core_text_by_file.values()):
        return emit_check_result(
            passed=False,
            findings=[
                "Structural check failed: could not read all core source files under "
                f"{src_root}."
            ],
        )
    if not app_main_text:
        return emit_check_result(
            passed=False,
            findings=[
                "Structural check failed: could not read app entrypoint at "
                f"{app_main_path}."
            ],
        )

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
    has_no_arg_evaluate_call = has_any_pattern(
        [r"\.\s*Evaluate\s*\(\s*\)"], scanned_main_text
    )
    has_arg_evaluate_call = has_any_pattern(
        [r"\.\s*Evaluate\s*\(\s*[^)\s]"], scanned_main_text
    )

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

    return emit_check_result(passed=not failures, findings=failures)


if __name__ == "__main__":
    raise SystemExit(main())
