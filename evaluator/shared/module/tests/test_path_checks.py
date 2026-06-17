#!/usr/bin/env python3

"""Unit tests for path_checks helpers."""

from __future__ import annotations

from pathlib import Path

from evaluator.shared.module.path_checks import (
    classify_relative_paths_against_baseline,
    find_missing_paths,
    find_missing_relative_paths,
    find_new_relative_paths,
    find_paths_with_disallowed_top_level,
    find_relative_paths_not_in_allowlist,
    normalize_text,
    read_text,
    scan_files,
)
from evaluator.shared.module.tests.base import ModuleTestCase


class PathChecksTest(ModuleTestCase):
    def test_normalize_text_normalizes_newlines_and_trailing_whitespace(self) -> None:
        text = "alpha  \r\nbeta\t\r\n\r\n"

        self.assertEqual(normalize_text(text), "alpha\nbeta\n")

    def test_read_text_returns_empty_string_for_missing_path_when_allowed(self) -> None:
        missing = self.repo_root / "missing.txt"

        self.assertEqual(read_text(missing), "")

    def test_find_missing_paths(self) -> None:
        present = self.case_root / "src/present.cc"
        self._write(self.case_root, "src/present.cc", "int value = 1;\n")

        missing_paths = find_missing_paths([present, self.case_root / "src/missing.cc"])

        self.assertEqual(missing_paths, [self.case_root / "src/missing.cc"])

    def test_find_missing_relative_paths(self) -> None:
        self._write(self.case_root, "src/present.cc", "int value = 1;\n")

        missing_relative = find_missing_relative_paths(
            self.case_root,
            ["src/present.cc", "src/missing.cc"],
        )

        self.assertEqual(missing_relative, ["src/missing.cc"])

    def test_find_new_relative_paths(self) -> None:
        self._write(self.case_root, "src/new.cc", "int value = 1;\n")
        self._write(self.case_root, "src/shared.cc", "same\n")
        self._write(self.baseline_root, "src/shared.cc", "same\n")

        created = find_new_relative_paths(
            self.case_root,
            self.baseline_root,
            ["src/new.cc", "src/shared.cc", "app/extra.cc"],
        )

        self.assertEqual(created, ["src/new.cc"])
        self.assertNotIn("src/shared.cc", created)

    def test_allowlist_helpers(self) -> None:
        disallowed_top_levels = find_paths_with_disallowed_top_level(
            ["src/new.cc", "app/extra.cc"],
            ["src"],
        )
        disallowed_relative_paths = find_relative_paths_not_in_allowlist(
            ["src/new.cc", "app/extra.cc"],
            ["src/new.cc"],
        )

        self.assertEqual(disallowed_top_levels, ["app/extra.cc"])
        self.assertEqual(disallowed_relative_paths, ["app/extra.cc"])

    def test_scan_files_accepts_directory_and_single_file_roots(self) -> None:
        self._write(self.case_root, "src/a.cc", "int a = 1;\n")
        self._write(self.case_root, "src/b.h", "int b = 2;\n")
        self._write(self.case_root, "src/ignore.txt", "ignored\n")

        scanned = scan_files(self.case_root / "src", self.case_root / "src/a.cc")

        self.assertEqual(
            scanned,
            [
                self.case_root / "src/a.cc",
                self.case_root / "src/b.h",
            ],
        )

    def test_classify_relative_paths_against_baseline(self) -> None:
        self._write(self.case_root, "src/modified.cc", "new\n")
        self._write(self.baseline_root, "src/modified.cc", "old\n")
        self._write(self.case_root, "src/created.cc", "created\n")
        self._write(self.baseline_root, "src/deleted.cc", "deleted\n")
        self._write(self.case_root, "src/shared.cc", "same\n")
        self._write(self.baseline_root, "src/shared.cc", "same\n")

        status = classify_relative_paths_against_baseline(
            self.case_root,
            self.baseline_root,
            [
                "src/modified.cc",
                "src/created.cc",
                "src/deleted.cc",
                "src/shared.cc",
                "src/missing_both.cc",
            ],
        )

        self.assertEqual(
            status.missing_in_root,
            ["src/deleted.cc", "src/missing_both.cc"],
        )
        self.assertEqual(
            status.missing_in_baseline,
            ["src/created.cc", "src/missing_both.cc"],
        )
        self.assertEqual(status.created_in_root, ["src/created.cc"])
        self.assertEqual(status.deleted_from_root, ["src/deleted.cc"])
        self.assertEqual(status.modified, ["src/modified.cc"])

    def test_read_text_raises_for_missing_path_when_not_allowed(self) -> None:
        with self.assertRaises(FileNotFoundError):
            read_text(self.repo_root / "missing.txt", missing_ok=False)


if __name__ == "__main__":
    import unittest

    unittest.main()
