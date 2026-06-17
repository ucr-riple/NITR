#!/usr/bin/env python3

"""Unit tests for BaselineDiffModule."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evaluator.shared.context import DefaultEvaluationContext
from evaluator.shared.module.baseline_diff_module import BaselineDiffModule


class BaselineDiffModuleTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name).resolve()
        self.case_root = (self.repo_root / "case").resolve()
        self.baseline_root = (self.repo_root / "baseline").resolve()
        self.case_root.mkdir(parents=True, exist_ok=True)
        self.baseline_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _context(self) -> DefaultEvaluationContext:
        return DefaultEvaluationContext(
            repo_root=self.repo_root,
            case_root=self.case_root,
            baseline_case_root=self.baseline_root,
            evaluator_root=self.repo_root / "evaluator_case",
            build_dir=self.repo_root / "build",
        )

    def _write_case(self, relative_path: str, content: str) -> None:
        self._write(self.case_root, relative_path, content)

    def _write_baseline(self, relative_path: str, content: str) -> None:
        self._write(self.baseline_root, relative_path, content)

    def _write(self, root: Path, relative_path: str, content: str) -> None:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _run_module(self, **config: object):
        module = BaselineDiffModule(
            name=str(config.get("name", "test_baseline_diff")),
            config=config,
        )
        return module.run(self._context())

    def test_identical_paths_pass(self) -> None:
        self._write_case("src/a.cc", "int value = 1;\n")
        self._write_baseline("src/a.cc", "int value = 1;\n")

        result = self._run_module(
            module_name="baseline_diff",
            paths=["src/a.cc"],
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.findings, [])
        self.assertEqual(result.details["checked_paths"], ["src/a.cc"])

    def test_reports_modified_path_without_allowlist(self) -> None:
        self._write_case("src/a.cc", "int value = 2;\n")
        self._write_baseline("src/a.cc", "int value = 1;\n")

        result = self._run_module(
            module_name="baseline_diff",
            paths=["src/a.cc"],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            ["Unexpected modified path relative to baseline: src/a.cc"],
        )

    def test_allows_created_path_by_top_level_directory(self) -> None:
        self._write_case("generated/new.cc", "int value = 1;\n")

        result = self._run_module(
            module_name="baseline_diff",
            paths=["generated/new.cc"],
            allowed_created_top_levels=["generated"],
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.findings, [])

    def test_reports_deleted_path_without_allowlist(self) -> None:
        self._write_baseline("src/a.cc", "int value = 1;\n")

        result = self._run_module(
            module_name="baseline_diff",
            paths=["src/a.cc"],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            ["Unexpected deleted path from case root: src/a.cc"],
        )

    def test_explicit_paths_do_not_scan_other_matching_files(self) -> None:
        self._write_case("src/in_scope.cc", "int value = 1;\n")
        self._write_baseline("src/in_scope.cc", "int value = 1;\n")
        self._write_case("src/out_of_scope.cc", "int value = 2;\n")
        self._write_baseline("src/out_of_scope.cc", "int value = 1;\n")

        result = self._run_module(
            module_name="baseline_diff",
            paths=["src/in_scope.cc"],
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.findings, [])
        self.assertEqual(result.details["checked_paths"], ["src/in_scope.cc"])

    def test_include_globs_and_exclude_globs_collect_expected_paths(self) -> None:
        self._write_case("src/a.cc", "int value = 1;\n")
        self._write_baseline("src/a.cc", "int value = 1;\n")
        self._write_case("src/skip.cc", "int value = 2;\n")
        self._write_baseline("src/skip.cc", "int value = 1;\n")
        self._write_case("app/kept.txt", "ignored\n")
        self._write_baseline("app/kept.txt", "ignored\n")

        result = self._run_module(
            module_name="baseline_diff",
            include_globs=["src/**/*", "app/**/*"],
            exclude_globs=["src/skip.cc"],
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.findings, [])
        self.assertEqual(result.details["checked_paths"], ["app/kept.txt", "src/a.cc"])


if __name__ == "__main__":
    unittest.main()
