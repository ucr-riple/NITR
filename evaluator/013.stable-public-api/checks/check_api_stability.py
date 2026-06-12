from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluator.shared.check_utils import case_root_from_script, read_text

HEADER = case_root_from_script(__file__) / "src" / "library_catalog.h"
text = read_text(HEADER, missing_ok=False)

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
