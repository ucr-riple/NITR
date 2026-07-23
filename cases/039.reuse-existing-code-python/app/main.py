from __future__ import annotations

from src.cosine_similarity import cosine_similarity


def main() -> None:
    print(cosine_similarity([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]))


if __name__ == "__main__":
    main()
