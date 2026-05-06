#!/usr/bin/env python3

import sys
from pathlib import Path

FORBIDDEN_TOKENS = [
    ".find(",
    ".substr(",
    ".compare(",
    ".find_first_of(",
    ".find_last_of(",
    ".starts_with(",
    "getline",
]


def main():
    if len(sys.argv) > 1:
        case_root = Path(sys.argv[1])
    else:
        case_root = (
            Path(__file__).resolve().parents[3]
            / "cases"
            / "024.recent-searches-categories"
        )

    impl_path = case_root / "src" / "recent_searches.cc"
    if not impl_path.exists():
        print(f"recent_searches.cc not found at {impl_path}")
        return 1

    failures = []
    inside_function = False

    for line_num, line in enumerate(impl_path.read_text().splitlines(), 1):
        if "RecentSearches::CountByCategory" in line:
            inside_function = True
            continue

        if not inside_function:
            continue

        if line.startswith("}"):
            inside_function = False
            continue

        for token in FORBIDDEN_TOKENS:
            if token in line:
                failures.append(
                    f"line {line_num}: CountByCategory body contains "
                    f"`{token}`. Move parsing into a separate helper."
                )

    if failures:
        print("Responsibility separation check failed:")
        for failure in failures:
            print(f"- {failure}")
        print(
            "\nCountByCategory should only loop over the buffer and "
            "compare categories. Move the string-parsing into its own "
            "helper method or function."
        )
        return 1

    print("Separation check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
