import sys
from pathlib import Path


FORMAT_OWNER_FILES = {
    "recent_searches.cc",
    "recent_searches.h",
    "search.cc",
    "search.h",
}

FORMAT_TOKENS = ["':'", '":"']

# reporter must call at least one of these 
RECENT_SEARCHES_API = ["CountByCategory", "CategoriesSeen", "CategoryOf"]


def main():
    if len(sys.argv) > 1:
        case_root = Path(sys.argv[1])
    else:
        case_root = (
            Path(__file__).resolve().parents[3]
            / "cases"
            / "025.recent-searches-categories"
        )

    src_dir = case_root / "src"
    if not src_dir.exists():
        print(f"src directory not found at {src_dir}")
        return 1

    failures = []

    source_files = sorted(src_dir.glob("*.cc")) + sorted(src_dir.glob("*.h"))
    for source_file in source_files:
        if source_file.name in FORMAT_OWNER_FILES:
            continue

        content = source_file.read_text()
        for token in FORMAT_TOKENS:
            if token in content:
                failures.append(
                    f"{source_file.name} contains {token}. format knowledge that should live on RecentSearches."
                )

    reporter_path = src_dir / "reporter.cc"
    if reporter_path.exists():
        reporter_text = reporter_path.read_text()

        reporter_calls_api = False
        for api_method in RECENT_SEARCHES_API:
            if api_method in reporter_text:
                reporter_calls_api = True
                break

        if not reporter_calls_api:
            api_list = ", ".join(RECENT_SEARCHES_API)
            failures.append(
                f"reporter.cc does not call any RecentSearches category API ({api_list}). Reporter must ask the data owner for category info instead of interpreting entries on its own."
            )

    if failures:
        print("Responsibility/Information Expert check failed:")
        for failure in failures:
            print(f"- {failure}")
        print(
            "\nRecentSearches owns the entry format. Code outside recent_searches and search must not parse entries directly.\n"
            "Use RecentSearches's API (CountByCategory, CategoriesSeen, or a public helper) instead of accessing\n"
            "the category prefix yourself."
        )
        return 1

    print("Separation/Information Expert check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
