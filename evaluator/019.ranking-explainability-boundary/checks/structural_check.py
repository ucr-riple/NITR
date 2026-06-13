#!/usr/bin/env python3
import argparse
import pathlib
import re
from typing import List

from evaluator.shared.path_checks import read_text
from evaluator.shared.source_analysis import has_any_substring, strip_comments


def remove_include_lines(text: str) -> str:
    """Drop include directives before scanning for display-oriented tokens."""
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#include")
    )


def string_literals(text: str) -> List[str]:
    """Extract string literals that may indicate leaked presentation concerns."""
    return re.findall(r'"(?:\\.|[^"\\])*"', text)


def struct_body(text: str, struct_name: str) -> str:
    """Return the body of a named struct for lightweight field counting."""
    match = re.search(rf"struct\s+{struct_name}\s*\{{(.*?)\}};", text, flags=re.S)
    if not match:
        return ""
    return match.group(1)


def count_field_lines(body: str) -> int:
    """Count likely field declarations in a struct body."""
    count = 0
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("//"):
            continue
        if line.endswith(";"):
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", type=pathlib.Path, default=pathlib.Path.cwd())
    args = parser.parse_args()

    root = args.case_root.resolve()
    src = root / "src"
    failures: List[str] = []

    ranker_text = strip_comments(
        remove_include_lines(
            read_text(src / "ranker.cc") + "\n" + read_text(src / "ranker.h")
        )
    )
    ranker_literals = string_literals(ranker_text)
    if ranker_literals:
        failures.append("ranker core should not contain display-oriented string literals")

    forbidden_ranker_includes = ["<sstream>", "<format>", "<iostream>"]
    ranker_sources = read_text(src / "ranker.cc") + "\n" + read_text(src / "ranker.h")
    if has_any_substring(forbidden_ranker_includes, ranker_sources):
        for header in forbidden_ranker_includes:
            if header in ranker_sources:
                failures.append(f"ranker core should not include {header}")

    suspicious_ranker_tokens = [
        "debug",
        "diagnostic",
        "trace",
        "message",
        "label",
        "render",
        "format",
    ]
    ranker_lower = ranker_text.lower()
    if has_any_substring(suspicious_ranker_tokens, ranker_lower):
        for token in suspicious_ranker_tokens:
            if token in ranker_lower:
                failures.append(
                    f"ranker core contains suspicious consumer-oriented token: {token}"
                )

    ranking_result_text = strip_comments(read_text(src / "ranking_result.h"))
    ranked_body = struct_body(ranking_result_text, "RankedItem")
    if not ranked_body:
        failures.append("ranking_result.h must define RankedItem")
    else:
        field_count = count_field_lines(ranked_body)
        if field_count > 3:
            failures.append("RankedItem should stay compact and not accumulate many fields")

    if has_any_substring(["std::string"], ranking_result_text):
        failures.append("ranking_result.h should not store display-oriented string fields")

    if has_any_substring(["std::vector"], ranking_result_text):
        failures.append("ranking_result.h should not store bulk diagnostic containers")

    item_text = strip_comments(read_text(src / "item.h")).lower()
    item_tokens = ["reason", "inspection", "diagnostic", "debug", "trace", "comparison"]
    if has_any_substring(item_tokens, item_text):
        for token in item_tokens:
            if token in item_text:
                failures.append(
                    f"item domain type should not absorb observer-oriented token: {token}"
                )

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print("structural checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
