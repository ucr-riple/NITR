#!/usr/bin/env python3

"""Run unit or integration tests as a pipeline module.

This module executes a test command, usually a `ctest` invocation, and turns
its process result into a structured module result. It also performs a small
amount of sanity checking to catch misconfigured or undiscovered tests.

Typical use cases:
- running one named `ctest` target after a `build` step
- verifying hidden/public evaluator test binaries were discovered correctly
- failing fast when a command reports that zero tests were found

Configuration shape:
- `module_name`: must be `"unit_test"`
- `name`: human-readable module instance name used in reports
- `command`: required test command; may be a string or argv-style list
- `cwd`: optional working directory; defaults to `context.repo_root`
- `env`: optional environment variable overrides

Execution behavior:
- resolves placeholders in command arguments and environment values
- runs the command as a subprocess without raising on non-zero exit
- treats any non-zero exit code as a module failure
- attempts to infer the expected number of tests from the command shape
- flags cases where the command appears to discover no tests, or fewer tests
  than expected, even if the process exit alone is ambiguous
- includes the tail of stdout/stderr in findings when the command fails

This module is intentionally focused on test execution and lightweight
discovery sanity checks. Build orchestration remains the responsibility of
`build`, and structural reasoning belongs in other modules.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path

from evaluator.shared.context import EvaluationContext
from evaluator.shared.module.base import EvaluationModule
from evaluator.shared.module.result import ModuleResult


class UnitTestModule(EvaluationModule):
    module_name = "unit_test"

    def evaluate(self, context: EvaluationContext) -> ModuleResult:
        command_config = self.config.get("command")
        if not command_config:
            raise ValueError(f"Module '{self.name}' requires a non-empty 'command'")

        if isinstance(command_config, str):
            command = shlex.split(self._format_string(command_config, context))
        else:
            command = [
                self._format_string(str(part), context) for part in command_config
            ]

        cwd_value = self.config.get("cwd")
        cwd = (
            self._resolve_path_value(cwd_value, context=context)
            if cwd_value
            else context.repo_root
        )
        merged_env = os.environ.copy()
        merged_env.update(context.env)
        merged_env.update(
            {
                key: self._format_string(str(value), context)
                for key, value in self.config.get("env", {}).items()
            }
        )

        completed = subprocess.run(
            command,
            cwd=cwd,
            env=merged_env,
            text=True,
            capture_output=True,
            check=False,
        )

        findings: list[str] = []
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()

        if completed.returncode != 0:
            findings.append(
                f"Command failed with exit code {completed.returncode}: {' '.join(command)}"
            )

        expected_tests = self._expected_test_count(command)
        detected_tests = self._detected_test_count(completed.stdout, completed.stderr)
        if expected_tests > 0 and self._has_no_tests_signal(
            completed.stdout, completed.stderr
        ):
            findings.append(
                f"Command reported no tests were found; expected at least {expected_tests}: {' '.join(command)}"
            )
        elif (
            expected_tests > 0
            and detected_tests is not None
            and detected_tests < expected_tests
        ):
            findings.append(
                f"Command reported only {detected_tests} tests; expected at least {expected_tests}: {' '.join(command)}"
            )

        if completed.returncode != 0 and stdout:
            findings.extend(f"stdout: {line}" for line in stdout.splitlines()[-20:])
        if completed.returncode != 0 and stderr:
            findings.extend(f"stderr: {line}" for line in stderr.splitlines()[-20:])
        if completed.returncode == 0 and findings and stdout:
            findings.extend(f"stdout: {line}" for line in stdout.splitlines()[-20:])
        if completed.returncode == 0 and findings and stderr:
            findings.extend(f"stderr: {line}" for line in stderr.splitlines()[-20:])

        return self._base_result(
            passed=completed.returncode == 0 and not findings,
            findings=findings,
            details={
                "command": command,
                "cwd": cwd.as_posix(),
                "returncode": completed.returncode,
                "expected_tests": expected_tests,
                "detected_tests": detected_tests,
            },
        )

    def _expected_test_count(self, command: list[str]) -> int:
        configured = self.config.get("min_expected_tests")
        if configured is not None:
            return int(configured)
        executable = Path(command[0]).name if command else ""
        return 1 if executable == "ctest" else 0

    def _has_no_tests_signal(self, stdout: str, stderr: str) -> bool:
        combined = f"{stdout}\n{stderr}"
        return "No tests were found!!!" in combined

    def _detected_test_count(self, stdout: str, stderr: str) -> int | None:
        combined = f"{stdout}\n{stderr}"
        match = re.search(r"Total Tests:\s*(\d+)", combined)
        if match:
            return int(match.group(1))
        if self._has_no_tests_signal(stdout, stderr):
            return 0
        return None
