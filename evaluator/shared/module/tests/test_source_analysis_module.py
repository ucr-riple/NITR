#!/usr/bin/env python3

"""Unit tests for SourceAnalysisModule."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evaluator.shared.context import DefaultEvaluationContext
from evaluator.shared.module.source_analysis_module import SourceAnalysisModule


class SourceAnalysisModuleTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name).resolve()
        self.case_root = (self.repo_root / "case").resolve()
        self.case_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _context(self) -> DefaultEvaluationContext:
        return DefaultEvaluationContext(
            repo_root=self.repo_root,
            case_root=self.case_root,
            baseline_case_root=self.case_root,
            evaluator_root=self.repo_root / "evaluator_case",
            build_dir=self.repo_root / "build",
        )

    def _write(self, relative_path: str, content: str) -> None:
        path = self.case_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _run_module(self, **config: object):
        module = SourceAnalysisModule(
            name=str(config.get("name", "test_source_analysis")),
            config=config,
        )
        return module.run(self._context())

    def test_reports_location_for_first_match(self) -> None:
        self._write(
            "src/example.cc",
            "\n\nconst int ForbiddenToken = 1;\n",
        )

        result = self._run_module(
            module_name="source_analysis",
            root="case_root",
            scan_roots=["src"],
            rules=[
                {
                    "id": "forbidden_token",
                    "any_substrings": ["ForbiddenToken"],
                    "message": "{location}",
                }
            ],
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.findings, ["src/example.cc:3"])

    def test_strip_comments_and_strings_avoids_false_positive(self) -> None:
        self._write(
            "src/example.cc",
            """
            // ForbiddenCall(
            const char* text = "ForbiddenCall(";
            int value = 1;
            """,
        )

        result = self._run_module(
            module_name="source_analysis",
            root="case_root",
            scan_roots=["src/example.cc"],
            normalize="strip_comments_and_strings",
            rules=[
                {
                    "id": "no_forbidden_call",
                    "any_patterns": [r"ForbiddenCall\s*\("],
                    "message": "matched",
                }
            ],
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.findings, [])

    def test_nested_all_of_any_of_and_not_rule(self) -> None:
        self._write("src/example.cc", "Alpha();\nBeta();\n")

        result = self._run_module(
            module_name="source_analysis",
            root="case_root",
            scan_roots=["src/example.cc"],
            rules=[
                {
                    "id": "nested_rule",
                    "all_of": [
                        {"any_substrings": ["Alpha"]},
                        {
                            "any_of": [
                                {"any_substrings": ["Missing"]},
                                {"any_substrings": ["Beta"]},
                            ]
                        },
                        {"not": {"any_substrings": ["Gamma"]}},
                    ],
                    "message": "nested matched",
                }
            ],
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.findings, ["nested matched"])

    def test_exclude_files_and_globs(self) -> None:
        self._write("src/a.cc", "ForbiddenToken\n")
        self._write("src/skip.cc", "ForbiddenToken\n")
        self._write("src/nested/ignored.cc", "ForbiddenToken\n")

        result = self._run_module(
            module_name="source_analysis",
            root="case_root",
            scan_roots=["src"],
            exclude_files=["skip.cc"],
            exclude_globs=["src/nested/*"],
            rules=[
                {
                    "id": "forbidden_token",
                    "any_substrings": ["ForbiddenToken"],
                    "message": "{relative_path}",
                }
            ],
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.findings, ["src/a.cc"])

    def test_global_rule_matching_file_count(self) -> None:
        self._write("src/a.h", "RequiredSeam\n")
        self._write("src/b.h", "RequiredSeam\n")

        result = self._run_module(
            module_name="source_analysis",
            root="case_root",
            scan_roots=["src"],
            global_rules=[
                {
                    "id": "seam_count",
                    "any_substrings": ["RequiredSeam"],
                    "max_matching_files": 1,
                    "message": "too many matches: {matching_file_count} in {matching_files}",
                }
            ],
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.findings,
            ["too many matches: 2 in src/a.h, src/b.h"],
        )

    def test_stop_on_first_match_returns_single_finding(self) -> None:
        self._write("src/a.cc", "ForbiddenToken\n")
        self._write("src/b.cc", "ForbiddenToken\n")

        result = self._run_module(
            module_name="source_analysis",
            root="case_root",
            scan_roots=["src"],
            stop_on_first_match=True,
            rules=[
                {
                    "id": "forbidden_token",
                    "any_substrings": ["ForbiddenToken"],
                    "message": "{relative_path}",
                }
            ],
        )

        self.assertFalse(result.passed)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0], "src/a.cc")


if __name__ == "__main__":
    unittest.main()
