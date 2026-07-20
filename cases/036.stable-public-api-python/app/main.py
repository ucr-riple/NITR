from __future__ import annotations

from src.library_catalog import Book, CatalogService


def main() -> None:
    service = CatalogService()
    books = [
        Book("b1", "Atlas", "Ada", False),
        Book("b2", "Archive of Fog", "Bea", True),
        Book("b3", "Atomic Habits", "James Clear", False),
    ]

    print("Matches:")
    for title in service.find_available_titles(books, "At"):
        print(f"  {title}")

    print()
    print(service.build_catalog_digest(books), end="")


if __name__ == "__main__":
    main()
