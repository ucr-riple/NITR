from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Book:
    id: str
    title: str
    author: str
    archived: bool = False


class CatalogService:
    def find_available_titles(self, books: list[Book], prefix: str) -> list[str]:
        matches = [book.title for book in books if book.title.startswith(prefix)]
        return sorted(matches)

    def build_catalog_digest(self, books: list[Book]) -> str:
        output = "Catalog Digest\n"
        for book in books:
            output += f"- {book.title} by {book.author}\n"
        return output
