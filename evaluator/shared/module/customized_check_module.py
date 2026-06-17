#!/usr/bin/env python3

"""Run a case-specific Python or shell check as a pipeline module.

This module exists for evaluator checks that are still too specialized to
express cleanly with the built-in declarative modules such as
`source_analysis`, `baseline_diff`, or `required_paths`.

Typical use cases:
- legacy per-case structural checks that have not yet been migrated
- checks that need cross-function or call-graph reasoning
- checks that need custom parsing, aggregation, or scoring logic
- checks that consume ad-hoc CLI arguments or environment variables

Configuration shape:
- `module_name`: must be `"customized_check"`
- `name`: human-readable module instance name used in reports
- `command`: required command to execute; may be a string or argv-style list
- `cwd`: optional working directory; defaults to `context.repo_root`
- `env`: optional environment variable overrides; values support placeholder
  expansion through the shared evaluation context formatter

Execution behavior:
- resolves placeholders like `{case_root}` and `{evaluator_root}` in command
  arguments and environment values
- runs the command as a subprocess without raising on non-zero exit
- treats any non-zero exit code as a module failure
- includes the last lines of stdout/stderr in findings when the command fails

This module is intentionally a fallback escape hatch. New checks should prefer
declarative modules when the rule can be represented there, and use
`customized_check` only when case-specific logic is genuinely required.
"""

from __future__ import annotations

import os
import shlex
import subprocess

from evaluator.shared.context import EvaluationContext
from evaluator.shared.module.base import EvaluationModule
from evaluator.shared.module.result import ModuleResult


class CustomizedCheckModule(EvaluationModule):
    module_name = "customized_check"

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
            },
        )
