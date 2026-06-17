#!/usr/bin/env python3

"""Unit tests for FrozenPathsModule."""

from __future__ import annotations

from evaluator.shared.module.frozen_paths_module import FrozenPathsModule
from evaluator.shared.module.tests.base import ModuleTestCase


class FrozenPathsModuleTest(ModuleTestCase):
    def _write_case(self, relative_path: str, content: str) -> None:
        self._write(self.case_root, relative_path, content)

    def _write_baseline(self, relative_path: str, content: str) -> None:
        self._write(self.baseline_root, relative_path, content)

    def _run_module(self, **config: object):
        module = FrozenPathsModule(
            name=str(config.get("name", "test_frozen_paths")),
            config=config,
        )
        return module.run(self._context())

    def test_identical_paths_pass(self) -> None:
        self._write_case("src/a.cc", "int value = 1;\n")
        self._write_baseline("src/a.cc", "int value = 1;\n")

        result = self._run_module(
            module_name="frozen_paths",
            paths=["src/a.cc"],
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.findings, [])
        self.assertEqual(result.details["checked_paths"], ["src/a.cc"])

    def test_reports_modified_path(self) -> None:
        self._write_case("src/a.cc", "int value = 2;\n")
        self._write_baseline("src/a.cc", "int value = 1;\n")

        result = self._run_module(
            module_name="frozen_paths",
            paths=["src/a.cc"],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            ["Frozen path unexpectedly modified: src/a.cc"],
        )

    def test_reports_created_path(self) -> None:
        self._write_case("src/new.cc", "int value = 1;\n")

        result = self._run_module(
            module_name="frozen_paths",
            paths=["src/new.cc"],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            [
                "Frozen path missing from baseline root: src/new.cc",
                "Frozen path unexpectedly created: src/new.cc",
            ],
        )

    def test_reports_deleted_path(self) -> None:
        self._write_baseline("src/old.cc", "int value = 1;\n")

        result = self._run_module(
            module_name="frozen_paths",
            paths=["src/old.cc"],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            [
                "Frozen path missing from case root: src/old.cc",
                "Frozen path unexpectedly deleted: src/old.cc",
            ],
        )

    def test_reports_missing_in_both_roots_once_per_side(self) -> None:
        result = self._run_module(
            module_name="frozen_paths",
            paths=["src/missing.cc"],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            [
                "Frozen path missing from case root: src/missing.cc",
                "Frozen path missing from baseline root: src/missing.cc",
            ],
        )

    def test_requires_non_empty_paths(self) -> None:
        result = self._run_module(
            module_name="frozen_paths",
            paths=[],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            ["frozen_paths module crashed: Module 'test_frozen_paths' requires a non-empty 'paths' list"],
        )


if __name__ == "__main__":
    unittest.main()
