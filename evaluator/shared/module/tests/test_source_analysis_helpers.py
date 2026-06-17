#!/usr/bin/env python3

"""Unit tests for source_analysis helper functions."""

from __future__ import annotations

import re

from evaluator.shared.module.source_analysis import (
    count_matching_patterns,
    count_matching_substrings,
    extract_function_body,
    find_class_body,
    find_matching_paths,
    find_matching_patterns,
    find_matching_substrings,
    find_missing_patterns,
    find_pattern_snippets,
    has_all_substrings,
    has_any_pattern,
    has_any_substring,
    include_paths,
    regex_matches,
    strip_comments,
    strip_comments_and_strings,
)
from evaluator.shared.module.tests.base import ModuleTestCase


class SourceAnalysisHelpersTest(ModuleTestCase):
    def test_has_any_substring(self) -> None:
        text = "Alpha Beta Gamma"

        self.assertTrue(has_any_substring(["Missing", "Beta"], text))

    def test_has_all_substrings(self) -> None:
        text = "Alpha Beta Gamma"

        self.assertTrue(has_all_substrings(["Alpha", "Gamma"], text))

    def test_find_matching_substrings(self) -> None:
        text = "Alpha Beta Gamma"

        self.assertEqual(
            find_matching_substrings(["Alpha", "Missing", "Gamma"], text),
            ["Alpha", "Gamma"],
        )

    def test_count_matching_substrings(self) -> None:
        text = "Alpha Beta Gamma"

        self.assertEqual(
            count_matching_substrings(["Alpha", "Missing", "Gamma"], text),
            2,
        )

    def test_regex_matches(self) -> None:
        text = "Alpha();\nBeta();\n"
        compiled = re.compile(r"Alpha\s*\(")

        self.assertTrue(regex_matches(compiled, text))

    def test_has_any_pattern(self) -> None:
        text = "Alpha();\nBeta();\n"

        self.assertTrue(has_any_pattern([r"Missing", r"Beta\s*\("], text))

    def test_find_matching_patterns(self) -> None:
        text = "Alpha();\nBeta();\n"

        self.assertEqual(
            find_matching_patterns([r"Alpha\s*\(", r"Missing"], text),
            [r"Alpha\s*\("],
        )

    def test_find_missing_patterns(self) -> None:
        text = "Alpha();\nBeta();\n"

        self.assertEqual(
            find_missing_patterns([r"Alpha\s*\(", r"Missing"], text),
            [r"Missing"],
        )

    def test_count_matching_patterns(self) -> None:
        text = "Alpha();\nBeta();\n"

        self.assertEqual(count_matching_patterns([r"Alpha\s*\(", r"Missing"], text), 1)

    def test_find_pattern_snippets_respects_max_chars(self) -> None:
        text = "ForbiddenCall(123);\nForbiddenCall(456);\n"

        self.assertEqual(
            find_pattern_snippets(r"ForbiddenCall\(\d+\)", text, max_chars=12),
            ["ForbiddenCal", "ForbiddenCal"],
        )

    def test_find_matching_paths_scans_directory_and_file_inputs(self) -> None:
        self._write(self.case_root, "src/a.cc", "ForbiddenCall();\n")
        self._write(self.case_root, "src/b.h", "int value = 1;\n")
        self._write(self.case_root, "src/c.txt", "ForbiddenCall();\n")

        # This helper is specifically responsible for traversing file-system
        # inputs, filtering by suffix, and then applying the regex. The regex
        # behavior itself is already covered by the string-only helpers above.
        matches = find_matching_paths(
            r"ForbiddenCall\s*\(",
            self.case_root / "src",
            self.case_root / "src/a.cc",
        )

        # Directory and explicit-file inputs are both scanned, so the same file can
        # appear twice when the caller passes overlapping roots.
        self.assertEqual(matches, [self.case_root / "src/a.cc", self.case_root / "src/a.cc"])

    def test_strip_comments(self) -> None:
        text = """
        // line comment
        const char* value = "ForbiddenCall()";
        /* block comment */
        int live_code = 1; // trailing comment
        char c = 'x';
        """

        stripped_comments = strip_comments(text)

        self.assertNotIn("// line comment", stripped_comments)
        self.assertNotIn("/* block comment */", stripped_comments)
        self.assertIn('"ForbiddenCall()"', stripped_comments)

    def test_strip_comments_and_strings(self) -> None:
        text = """
        // line comment
        const char* value = "ForbiddenCall()";
        /* block comment */
        int live_code = 1; // trailing comment
        char c = 'x';
        """

        stripped_all = strip_comments_and_strings(text)

        self.assertIn('""', stripped_all)
        self.assertIn("''", stripped_all)
        self.assertNotIn("ForbiddenCall()", stripped_all)

    def test_include_paths_extracts_cxx_includes(self) -> None:
        text = """
        #include "src/foo.h"
        # include <vector>
        #include "bar/baz.h"
        """

        self.assertEqual(
            include_paths(text),
            ["src/foo.h", "vector", "bar/baz.h"],
        )

    def test_find_class_body_handles_nested_braces(self) -> None:
        text = """
        class Example {
         public:
          void Run() {
            if (true) {
              value_ = 1;
            }
          }
        };
        """

        body = find_class_body(text, "Example")

        self.assertIsNotNone(body)
        self.assertIn("void Run()", body)
        self.assertIn("value_ = 1;", body)

    def test_extract_function_body(self) -> None:
        text = """
        void Existing() {
          if (true) {
            value = 1;
          }
        }
        """

        self.assertIn("value = 1;", extract_function_body(text, "Existing"))

    def test_extract_function_body_returns_empty_string_for_missing_function(self) -> None:
        text = """
        void Existing() {
          value = 1;
        }
        """

        self.assertEqual(extract_function_body(text, "Missing"), "")


if __name__ == "__main__":
    import unittest

    unittest.main()
