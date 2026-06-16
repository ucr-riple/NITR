#!/usr/bin/env python3

"""Unit-test evaluation module."""

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
        if expected_tests > 0 and self._has_no_tests_signal(completed.stdout, completed.stderr):
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
