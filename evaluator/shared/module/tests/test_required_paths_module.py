#!/usr/bin/env python3

"""Unit tests for RequiredPathsModule."""

from __future__ import annotations

from pathlib import Path

from evaluator.shared.module.required_paths_module import RequiredPathsModule
from evaluator.shared.module.tests.base import ModuleTestCase


class RequiredPathsModuleTest(ModuleTestCase):
    def _run_module(self, **config: object):
        module = RequiredPathsModule(
            name=str(config.get("name", "test_required_paths")),
            config=config,
        )
        return module.run(self._context())

    def test_passes_when_all_required_paths_exist_under_case_root(self) -> None:
        self._write(self.case_root, "src/a.cc", "int value = 1;\n")
        self._mkdir(self.case_root, "tests")

        result = self._run_module(
            module_name="required_paths",
            paths=["src/a.cc", "tests"],
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.findings, [])
        self.assertEqual(result.details["root"], self.case_root.as_posix())
        self.assertEqual(result.details["checked_paths"], ["src/a.cc", "tests"])

    def test_reports_each_missing_required_path(self) -> None:
        self._write(self.case_root, "src/present.cc", "int value = 1;\n")

        result = self._run_module(
            module_name="required_paths",
            paths=["src/present.cc", "src/missing.cc", "tests/missing"],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            [
                f"Missing required path under {self.case_root.as_posix()}: src/missing.cc",
                f"Missing required path under {self.case_root.as_posix()}: tests/missing",
            ],
        )

    def test_uses_configured_root_selector(self) -> None:
        self._write(self.baseline_root, "src/reference.cc", "int value = 1;\n")

        result = self._run_module(
            module_name="required_paths",
            root="baseline_case_root",
            paths=["src/reference.cc"],
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.findings, [])
        self.assertEqual(result.details["root"], self.baseline_root.as_posix())

    def test_requires_non_empty_paths(self) -> None:
        result = self._run_module(
            module_name="required_paths",
            paths=[],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            ["required_paths module crashed: Module 'test_required_paths' requires a non-empty 'paths' list"],
        )

    def test_reports_invalid_root_selector(self) -> None:
        result = self._run_module(
            module_name="required_paths",
            root="unknown_root",
            paths=["src/a.cc"],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            ["required_paths module crashed: Context root 'unknown_root' is not available for module 'test_required_paths'"],
        )


if __name__ == "__main__":
    unittest.main()
