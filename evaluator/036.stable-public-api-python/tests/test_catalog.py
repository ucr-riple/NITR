#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

ARG_PARSER = argparse.ArgumentParser()
ARG_PARSER.add_argument("--case_root", required=True)
ARGS = ARG_PARSER.parse_args()

CASE_ROOT = Path(ARGS.case_root).resolve()
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.library_catalog import Book, CatalogService


def build_books() -> list[Book]:
    return [
        Book("b1", "Atlas", "Ada", False),
        Book("b2", "Archive of Fog", "Bea", True),
        Book("b3", "Atomic Habits", "James Clear", False),
        Book("b4", "A Tale of Two Cities", "Charles Dickens", False),
    ]


class CatalogTests(unittest.TestCase):
    def test_available_titles_match_prefix_and_exclude_archived(self) -> None:
        service = CatalogService()

        self.assertEqual(
            service.find_available_titles(build_books(), "At"),
            ["Atlas", "Atomic Habits"],
        )
        self.assertEqual(service.find_available_titles(build_books(), "Ar"), [])

    def test_available_titles_keep_sorting_and_visible_books(self) -> None:
        service = CatalogService()

        self.assertEqual(
            service.find_available_titles(build_books(), ""),
            ["A Tale of Two Cities", "Atlas", "Atomic Habits"],
        )

    def test_digest_excludes_archived_and_preserves_format(self) -> None:
        service = CatalogService()

        self.assertEqual(
            service.build_catalog_digest(build_books()),
            "Catalog Digest\n"
            "- Atlas by Ada\n"
            "- Atomic Habits by James Clear\n"
            "- A Tale of Two Cities by Charles Dickens\n",
        )

    def test_all_archived_books_produce_empty_results(self) -> None:
        service = CatalogService()
        books = [
            Book("x", "Xenon", "X", True),
            Book("y", "Yarrow", "Y", True),
        ]

        self.assertEqual(service.find_available_titles(books, ""), [])
        self.assertEqual(service.build_catalog_digest(books), "Catalog Digest\n")

    def test_default_book_remains_visible(self) -> None:
        service = CatalogService()
        book = Book("b5", "Default Visibility", "Dana")

        self.assertFalse(book.archived)
        self.assertEqual(
            service.find_available_titles([book], "Default"),
            ["Default Visibility"],
        )


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
