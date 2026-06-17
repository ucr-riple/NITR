#!/usr/bin/env python3

"""Unit tests for BuildModule."""

from __future__ import annotations

import shlex
import sys
import textwrap
from pathlib import Path

from evaluator.shared.module.build_module import BuildModule
from evaluator.shared.module.tests.base import ModuleTestCase


class BuildModuleTest(ModuleTestCase):
    def _run_module(
        self,
        *,
        context=None,
        **config: object,
    ):
        module = BuildModule(
            name=str(config.get("name", "test_build")),
            config=config,
        )
        return module.run(context or self._context())

    def test_runs_build_command_successfully(self) -> None:
        (self.build_dir / "CMakeCache.txt").write_text("cached\n", encoding="utf-8")
        output_path = self.repo_root / "build_ran.txt"

        result = self._run_module(
            module_name="build",
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
        (self.build_dir / "CMakeCache.txt").write_text("cached\n", encoding="utf-8")
        output_path = self.repo_root / "formatted.txt"

        result = self._run_module(
            module_name="build",
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

    def test_runs_configure_step_when_cmake_cache_is_missing(self) -> None:
        configure_log = self.repo_root / "configure.log"
        build_output = self.repo_root / "build_after_configure.txt"
        fake_cmake = self.bin_dir / "cmake"
        self._write_executable(
            fake_cmake,
            textwrap.dedent(
                f"""\
                #!/bin/sh
                echo "$@" > {shlex.quote(str(configure_log))}
                exit 0
                """
            ),
        )

        context = self._context(env={"PATH": self.bin_dir.as_posix()})
        result = self._run_module(
            context=context,
            module_name="build",
            configure_args=["-DCUSTOM=ON"],
            command=[
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    f"Path({str(build_output)!r}).write_text('built', encoding='utf-8')"
                ),
            ],
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.details["configure_returncode"], 0)
        self.assertEqual(result.details["returncode"], 0)
        self.assertEqual(
            result.details["configure_command"],
            [
                "cmake",
                "-S",
                self.repo_root.as_posix(),
                "-B",
                self.build_dir.as_posix(),
                "-DCUSTOM=ON",
            ],
        )
        configure_output = configure_log.read_text(encoding="utf-8")
        self.assertIn(f"-S {self.repo_root.as_posix()}", configure_output)
        self.assertIn(f"-B {self.build_dir.as_posix()}", configure_output)
        self.assertTrue(build_output.exists())

    def test_skips_configure_when_cmake_cache_exists(self) -> None:
        (self.build_dir / "CMakeCache.txt").write_text("cached\n", encoding="utf-8")
        fake_cmake = self.bin_dir / "cmake"
        configure_marker = self.repo_root / "configure_should_not_run.txt"
        self._write_executable(
            fake_cmake,
            textwrap.dedent(
                f"""\
                #!/bin/sh
                echo ran > {shlex.quote(str(configure_marker))}
                exit 0
                """
            ),
        )
        build_output = self.repo_root / "build_only.txt"

        context = self._context(env={"PATH": self.bin_dir.as_posix()})
        result = self._run_module(
            context=context,
            module_name="build",
            command=[
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    f"Path({str(build_output)!r}).write_text('built', encoding='utf-8')"
                ),
            ],
        )

        self.assertTrue(result.passed)
        self.assertNotIn("configure_command", result.details)
        self.assertFalse(configure_marker.exists())
        self.assertTrue(build_output.exists())

    def test_returns_failure_when_configure_step_fails(self) -> None:
        configure_marker = self.repo_root / "configure_failed.txt"
        build_marker = self.repo_root / "build_should_not_run.txt"
        fake_cmake = self.bin_dir / "cmake"
        self._write_executable(
            fake_cmake,
            textwrap.dedent(
                f"""\
                #!/bin/sh
                echo "bad configure" >&2
                echo failed > {shlex.quote(str(configure_marker))}
                exit 7
                """
            ),
        )

        context = self._context(env={"PATH": self.bin_dir.as_posix()})
        result = self._run_module(
            context=context,
            module_name="build",
            command=[
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    f"Path({str(build_marker)!r}).write_text('ran', encoding='utf-8')"
                ),
            ],
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.details["configure_returncode"], 7)
        self.assertEqual(
            result.findings[0],
            f"Build configure command failed with exit code 7: cmake -S {self.repo_root.as_posix()} -B {self.build_dir.as_posix()} -DNITR_BUILD_EVALUATOR=ON",
        )
        self.assertIn("stderr: bad configure", result.findings)
        self.assertTrue(configure_marker.exists())
        self.assertFalse(build_marker.exists())

    def test_requires_non_empty_command(self) -> None:
        result = self._run_module(
            module_name="build",
            command=[],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            ["build module crashed: Module 'test_build' requires a non-empty 'command'"],
        )


if __name__ == "__main__":
    unittest.main()
