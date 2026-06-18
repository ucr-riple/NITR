#!/usr/bin/env python3

"""Build case targets as a pipeline module.

This module is responsible for compiling the case and evaluator binaries needed
by downstream modules, usually before `unit_test` or other checks that depend
on produced executables or compiled objects.

Typical use cases:
- building one or more case-specific test targets before running `ctest`
- compiling evaluator helper binaries required by a case
- lazily configuring a staged workspace when no CMake cache exists yet

Configuration shape:
- `module_name`: must be `"build"`
- `name`: human-readable module instance name used in reports
- `command`: required build command; may be a string or argv-style list
- `cwd`: optional working directory; defaults to `context.repo_root`
- `env`: optional environment variable overrides
- `configure_args`: optional extra arguments for the initial `cmake -S/-B`
  configure step; defaults to `-DNITR_BUILD_EVALUATOR=ON`

Execution behavior:
- resolves placeholders in command arguments, configure args, and environment
- if `context.build_dir` exists but has no `CMakeCache.txt`, runs an initial
  `cmake -S <repo_root> -B <build_dir>` configure step first
- then runs the configured build command as a subprocess
- treats any non-zero configure/build exit code as a module failure
- includes the tail of stdout/stderr in findings when configure/build fails

This module is intentionally focused on build orchestration only. It does not
try to interpret test outcomes or structural constraints; those belong in
`unit_test`, `source_analysis`, or other dedicated modules.
"""

from __future__ import annotations

import os
import shlex
import subprocess

from evaluator.shared.context import EvaluationContext
from evaluator.shared.module.base import EvaluationModule
from evaluator.shared.module.result import ModuleResult


class BuildModule(EvaluationModule):
    module_name = "build"

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

        configure_details: dict[str, object] = {}
        if (
            context.build_dir is not None
            and not (context.build_dir / "CMakeCache.txt").exists()
        ):
            configure_args = [
                self._format_string(str(value), context)
                for value in self.config.get(
                    "configure_args", ["-DNITR_BUILD_EVALUATOR=ON"]
                )
            ]
            configure_command = [
                "cmake",
                "-S",
                context.repo_root.as_posix(),
                "-B",
                context.build_dir.as_posix(),
                *configure_args,
            ]
            configured = subprocess.run(
                configure_command,
                cwd=cwd,
                env=merged_env,
                text=True,
                capture_output=True,
                check=False,
            )
            configure_details = {
                "configure_command": configure_command,
                "configure_returncode": configured.returncode,
            }
            if configured.returncode != 0:
                findings = [
                    f"Build configure command failed with exit code {configured.returncode}: {' '.join(configure_command)}"
                ]
                if configured.stdout.strip():
                    findings.extend(
                        f"stdout: {line}"
                        for line in configured.stdout.strip().splitlines()[-20:]
                    )
                if configured.stderr.strip():
                    findings.extend(
                        f"stderr: {line}"
                        for line in configured.stderr.strip().splitlines()[-20:]
                    )
                return self._base_result(
                    passed=False,
                    findings=findings,
                    details={
                        "command": command,
                        "cwd": cwd.as_posix(),
                        **configure_details,
                    },
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
                f"Build command failed with exit code {completed.returncode}: {' '.join(command)}"
            )
        if completed.returncode != 0 and stdout:
            findings.extend(f"stdout: {line}" for line in stdout.splitlines()[-20:])
        if completed.returncode != 0 and stderr:
            findings.extend(f"stderr: {line}" for line in stderr.splitlines()[-20:])

        return self._base_result(
            passed=completed.returncode == 0 and not findings,
            findings=findings,
            details={
                "command": command,
                "cwd": cwd.as_posix(),
                "returncode": completed.returncode,
                **configure_details,
            },
        )
