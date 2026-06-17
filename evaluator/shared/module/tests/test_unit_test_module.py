#!/usr/bin/env python3

"""Unit tests for UnitTestModule."""

from __future__ import annotations

import sys
import textwrap

from evaluator.shared.module.unit_test_module import UnitTestModule
from evaluator.shared.module.tests.base import ProcessModuleTestCase


class UnitTestModuleTest(ProcessModuleTestCase):
    def _run_module(
        self,
        *,
        context=None,
        **config: object,
    ):
        module = UnitTestModule(
            name=str(config.get("name", "test_unit_test")),
            config=config,
        )
        return module.run(context or self._context())

    def test_runs_command_successfully(self) -> None:
        output_path = self.repo_root / "unit_test_ran.txt"

        result = self._run_module(
            module_name="unit_test",
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
        self.assertEqual(result.details["expected_tests"], 0)
        self.assertIsNone(result.details["detected_tests"])
        self.assertTrue(output_path.exists())

    def test_formats_command_env_and_cwd(self) -> None:
        output_path = self.repo_root / "formatted_unit_test.txt"

        result = self._run_module(
            module_name="unit_test",
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
            module_name="unit_test",
            command=[
                sys.executable,
                "-c",
                "import sys; print('failing stdout'); print('failing stderr', file=sys.stderr); raise SystemExit(3)",
            ],
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.details["returncode"], 3)
        self.assertEqual(
            result.findings[0],
            f"Command failed with exit code 3: {sys.executable} -c import sys; print('failing stdout'); print('failing stderr', file=sys.stderr); raise SystemExit(3)",
        )
        self.assertIn("stdout: failing stdout", result.findings)
        self.assertIn("stderr: failing stderr", result.findings)

    def test_ctest_no_tests_signal_fails_even_with_zero_exit(self) -> None:
        fake_ctest = self.bin_dir / "ctest"
        self._write_executable(
            fake_ctest,
            "#!/bin/sh\nprintf 'No tests were found!!!\\n'\nexit 0\n",
        )
        result = self._run_module(
            context=self._context(env={"PATH": self.bin_dir.as_posix()}),
            module_name="unit_test",
            command=[
                "ctest",
                "--output-on-failure",
            ],
            min_expected_tests=1,
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.details["expected_tests"], 1)
        self.assertEqual(result.details["detected_tests"], 0)
        self.assertEqual(
            result.findings,
            [
                "Command reported no tests were found; expected at least 1: ctest --output-on-failure",
                "stdout: No tests were found!!!",
            ],
        )

    def test_min_expected_tests_reports_too_few_detected_tests(self) -> None:
        result = self._run_module(
            module_name="unit_test",
            min_expected_tests=3,
            command=[
                sys.executable,
                "-c",
                "print('Total Tests: 2')",
            ],
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.details["expected_tests"], 3)
        self.assertEqual(result.details["detected_tests"], 2)
        self.assertEqual(
            result.findings,
            [
                f"Command reported only 2 tests; expected at least 3: {sys.executable} -c print('Total Tests: 2')",
                "stdout: Total Tests: 2",
            ],
        )

    def test_ctest_defaults_to_one_expected_test(self) -> None:
        fake_ctest = self.bin_dir / "ctest"
        self._write_executable(
            fake_ctest,
            "#!/bin/sh\nprintf 'No tests were found!!!\\n'\nexit 0\n",
        )
        result = self._run_module(
            context=self._context(env={"PATH": self.bin_dir.as_posix()}),
            module_name="unit_test",
            command=[
                "ctest",
                "-R",
                "^case001_tests$",
            ],
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.details["expected_tests"], 1)
        self.assertEqual(result.details["detected_tests"], 0)
        self.assertEqual(
            result.findings,
            [
                "Command reported no tests were found; expected at least 1: ctest -R ^case001_tests$",
                "stdout: No tests were found!!!",
            ],
        )

    def test_requires_non_empty_command(self) -> None:
        result = self._run_module(
            module_name="unit_test",
            command=[],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            ["unit_test module crashed: Module 'test_unit_test' requires a non-empty 'command'"],
        )


if __name__ == "__main__":
    unittest.main()
