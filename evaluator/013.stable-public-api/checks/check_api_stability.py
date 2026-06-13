import re

from evaluator.shared.path_checks import (
    case_root_from_script,
    read_text,
)
from evaluator.shared.source_analysis import find_missing_patterns
from evaluator.shared.check_output import emit_check_result

FORBIDDEN_FLAGS = [
    "include_archived",
    "show_archived",
    "archived_mode",
    "includeArchived",
]

REQUIRED_SIGNATURES = {
    "FindAvailableTitles signature": r"std::vector<std::string>\s+FindAvailableTitles\s*\(\s*const std::vector<Book>& books,\s*const std::string& prefix\s*\)\s*const;",
    "BuildCatalogDigest signature": r"std::string\s+BuildCatalogDigest\s*\(\s*const std::vector<Book>& books\s*\)\s*const;",
}


def main() -> int:
    header = case_root_from_script(__file__) / "src" / "library_catalog.h"
    text = read_text(header, missing_ok=False)
    violations = []

    for flag in FORBIDDEN_FLAGS:
        if flag in text:
            violations.append(f"Forbidden public API control flag detected: {flag}")

    missing_signatures = find_missing_patterns(
        REQUIRED_SIGNATURES.values(), text, flags=re.MULTILINE
    )
    if missing_signatures:
        missing_descriptions = [
            description
            for description, pattern in REQUIRED_SIGNATURES.items()
            if pattern in missing_signatures
        ]
        violations.append(
            "Public API signature changed unexpectedly: "
            + ", ".join(missing_descriptions)
        )

    return emit_check_result(passed=not violations, findings=violations)


if __name__ == "__main__":
    raise SystemExit(main())
