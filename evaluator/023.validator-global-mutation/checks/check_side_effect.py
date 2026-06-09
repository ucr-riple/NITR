#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


APP_MAIN_EXPECTED = """#include <iostream>
#include <vector>

#include "grader.h"
#include "reporter.h"
#include "stats.h"
#include "submission.h"
#include "validator.h"

int main() {
    using namespace nitr::case023;

    const std::vector<Submission> submissions = {
        {"alice", "Well-structured solution", false},
        {"bob", "", false},
        {"carol", "Late but complete", true},
        {"dana", "Concise answer", false},
    };

    Grader grader;
    Validator validator;

    for (const Submission& submission : submissions) {
        if (!validator.validate(submission)) {
            continue;
        }

        ++total_processed;
        std::cout << submission.student_id << ": " << grader.Grade(submission) << '\\n';
    }

    Reporter reporter;
    std::cout << reporter.Summary() << '\\n';
    return 0;
}
"""

GRADER_CC_EXPECTED = """#include "grader.h"

#include <algorithm>

namespace nitr::case023 {

int Grader::Grade(const Submission& s) const {
    const int length_score = static_cast<int>(std::min<std::size_t>(s.content.size(), 100));
    return length_score;
}

}  // namespace nitr::case023
"""

REPORTER_CC_EXPECTED = """#include "reporter.h"

#include <string>

#include "stats.h"

namespace nitr::case023 {

std::string Reporter::Summary() const {
    return "Processed " + std::to_string(total_processed) + " submissions";
}

}  // namespace nitr::case023
"""


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def strip_comments_and_strings(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    text = re.sub(r"'(?:\\.|[^'\\])+'", "''", text)
    return text


def include_paths(text: str) -> list[str]:
    includes: list[str] = []
    for line in text.splitlines():
        match = re.match(r'^\s*#\s*include\s*[<"]([^">]+)[">]', line)
        if match:
            includes.append(match.group(1))
    return includes


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").strip() + "\n"


def main() -> int:
    if len(sys.argv) > 1:
        case_root = Path(sys.argv[1]).resolve()
    else:
        repo_root = Path(__file__).resolve().parents[3]
        case_root = repo_root / "cases" / "023.validator-global-mutation"

    src_root = case_root / "src"
    app_root = case_root / "app"
    validator_files = [
        src_root / "validator.h",
        src_root / "validator.cc",
    ]
    frozen_files = {
        app_root / "main.cc": APP_MAIN_EXPECTED,
        src_root / "grader.cc": GRADER_CC_EXPECTED,
        src_root / "reporter.cc": REPORTER_CC_EXPECTED,
    }
    allowed_total_processed_refs = {
        src_root / "stats.h",
        src_root / "stats.cc",
        src_root / "reporter.cc",
        app_root / "main.cc",
    }
    allowed_stats_includes = {
        src_root / "stats.cc",
        src_root / "reporter.cc",
        app_root / "main.cc",
    }

    failures: list[str] = []

    for path in validator_files:
        raw_text = read_text(path)
        if not raw_text:
            failures.append(f"{path.name}: missing or unreadable validator file.")
            continue

        scanned_text = strip_comments_and_strings(raw_text)
        includes = include_paths(raw_text)

        if any(include.endswith("stats.h") for include in includes):
            failures.append(
                f"{path.name}: Validator must not include stats.h directly."
            )

        if any(include.startswith("src/") for include in includes):
            failures.append(
                f'{path.name}: do not use #include "src/..."; keep starter relative '
                "include style."
            )

        if re.search(r"\btotal_processed\b", scanned_text):
            failures.append(
                f"{path.name}: Validator must not reference total_processed."
            )

    source_files = sorted(src_root.glob("*.h")) + sorted(src_root.glob("*.cc"))
    source_files.append(app_root / "main.cc")
    for path in source_files:
        raw_text = read_text(path)
        if not raw_text:
            failures.append(
                f"{path.relative_to(case_root)}: missing or unreadable file."
            )
            continue

        scanned_text = strip_comments_and_strings(raw_text)
        includes = include_paths(raw_text)

        if path not in allowed_total_processed_refs and re.search(
            r"\btotal_processed\b", scanned_text
        ):
            failures.append(
                f"{path.relative_to(case_root)}: total_processed must stay owned by stats/reporter/main only."
            )

        if path not in allowed_stats_includes and any(
            include.endswith("stats.h") for include in includes
        ):
            failures.append(
                f"{path.relative_to(case_root)}: stats.h may only be included by reporter.cc, stats.cc, or app/main.cc."
            )

    for path, expected_text in frozen_files.items():
        actual_text = read_text(path)
        if not actual_text:
            failures.append(
                f"{path.relative_to(case_root)}: missing required starter file."
            )
            continue

        if normalize_text(actual_text) != normalize_text(expected_text):
            failures.append(
                f"{path.relative_to(case_root)}: must remain unchanged from the starter code."
            )

    if failures:
        print("Maintainability check failed:")
        for failure in failures:
            print(f"- {failure}")
        print(
            "Validator should only inspect Submission and return a boolean. "
            "The total_processed counter belongs in app/main.cc, while "
            "Reporter only reads it. Do not move counter ownership into "
            "validator or other helpers."
        )
        return 1

    print("Side-effect check passed: Validator remains decoupled from global stats.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
