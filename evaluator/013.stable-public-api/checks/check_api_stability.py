from pathlib import Path
import re
import sys

HEADER = (
    Path(__file__).resolve().parents[3]
    / "cases"
    / Path(__file__).resolve().parents[1].name
    / "src"
    / "library_catalog.h"
)
text = HEADER.read_text()

for forbidden in [
    "include_archived",
    "show_archived",
    "archived_mode",
    "includeArchived",
]:
    if forbidden in text:
        print(f"Forbidden public API control flag detected: {forbidden}")
        sys.exit(1)

patterns = [
    r"std::vector<std::string>\s+FindAvailableTitles\s*\(\s*const std::vector<Book>& books,\s*const std::string& prefix\s*\)\s*const;",
    r"std::string\s+BuildCatalogDigest\s*\(\s*const std::vector<Book>& books\s*\)\s*const;",
]

for pattern in patterns:
    if re.search(pattern, text, re.MULTILINE) is None:
        print("Public API signature changed unexpectedly.")
        sys.exit(1)

print("API stability check passed.")
