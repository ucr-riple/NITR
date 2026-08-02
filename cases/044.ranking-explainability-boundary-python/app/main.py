from src.models import Item
from src.ranker import Ranker


def main() -> None:
    print(Ranker().rank([Item(1, "Example", 50, True, 1, 10, False)]))


if __name__ == "__main__":
    main()
