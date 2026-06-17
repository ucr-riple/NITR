#!/usr/bin/env python3

"""Unit tests for CustomizedCheckModule."""

from __future__ import annotations

import sys
import textwrap

from evaluator.shared.module.customized_check_module import CustomizedCheckModule
from evaluator.shared.module.tests.base import ModuleTestCase


class CustomizedCheckModuleTest(ModuleTestCase):
    def _run_module(
        self,
        *,
        context=None,
        **config: object,
    ):
        module = CustomizedCheckModule(
            name=str(config.get("name", "test_customized_check")),
            config=config,
        )
        return module.run(context or self._context())

    def test_runs_command_successfully(self) -> None:
        output_path = self.repo_root / "custom_check_ran.txt"

        result = self._run_module(
            module_name="customized_check",
            command=[
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    f"Path({str(output_path)!r}).write_text('ok', encoding='utf-8')"
                ),
            ],
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.findings, [])
        self.assertEqual(result.details["returncode"], 0)
        self.assertTrue(output_path.exists())

    def test_formats_command_env_and_cwd(self) -> None:
        output_path = self.repo_root / "formatted_custom_check.txt"

        result = self._run_module(
            module_name="customized_check",
            cwd="{case_root}",
            env={"EXPECTED_CASE_ROOT": "{case_root}"},
            command=[
                sys.executable,
                "-c",
                textwrap.dedent(
                    f"""
                    import os
                    from pathlib import Path
                    assert os.getcwd() == {self.case_root.as_posix()!r}
                    assert os.environ["EXPECTED_CASE_ROOT"] == {self.case_root.as_posix()!r}
                    Path({str(output_path)!r}).write_text("ok", encoding="utf-8")
                    """
                ),
            ],
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.details["cwd"], self.case_root.as_posix())
        self.assertTrue(output_path.exists())

    def test_reports_non_zero_exit_and_output_tail(self) -> None:
        result = self._run_module(
            module_name="customized_check",
            command=[
                sys.executable,
                "-c",
                "import sys; print('failing stdout'); print('failing stderr', file=sys.stderr); raise SystemExit(5)",
            ],
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.details["returncode"], 5)
        self.assertEqual(
            result.findings[0],
            f"Command failed with exit code 5: {sys.executable} -c import sys; print('failing stdout'); print('failing stderr', file=sys.stderr); raise SystemExit(5)",
        )
        self.assertIn("stdout: failing stdout", result.findings)
        self.assertIn("stderr: failing stderr", result.findings)

    def test_requires_non_empty_command(self) -> None:
        result = self._run_module(
            module_name="customized_check",
            command=[],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            [
                "customized_check module crashed: Module 'test_customized_check' requires a non-empty 'command'"
            ],
        )


if __name__ == "__main__":
    unittest.main()
