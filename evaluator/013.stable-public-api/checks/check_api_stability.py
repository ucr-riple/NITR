import re

from evaluator.shared.check_utils import case_root_from_script, read_text

FORBIDDEN_FLAGS = [
    "include_archived",
    "show_archived",
    "archived_mode",
    "includeArchived",
]

REQUIRED_SIGNATURES = [
    r"std::vector<std::string>\s+FindAvailableTitles\s*\(\s*const std::vector<Book>& books,\s*const std::string& prefix\s*\)\s*const;",
    r"std::string\s+BuildCatalogDigest\s*\(\s*const std::vector<Book>& books\s*\)\s*const;",
]


def main() -> int:
    header = case_root_from_script(__file__) / "src" / "library_catalog.h"
    text = read_text(header, missing_ok=False)
    violations = []

    for flag in FORBIDDEN_FLAGS:
        if flag in text:
            violations.append(f"Forbidden public API control flag detected: {flag}")

    for pattern in REQUIRED_SIGNATURES:
        if re.search(pattern, text, re.MULTILINE) is None:
            violations.append("Public API signature changed unexpectedly.")

    for v in violations:
        print(v)
    if violations:
        return 1
    print("API stability check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
