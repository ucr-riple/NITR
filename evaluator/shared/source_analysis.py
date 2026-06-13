from __future__ import annotations

"""Shared helpers for content-level evaluator checks.

These helpers support checks that inspect source text for structural or semantic
signals, such as:
- whether required or forbidden tokens/patterns appear
- which files under a tree contain a matching signal
- lightweight source normalization before pattern matching
- extracting class/function bodies for local structural assertions
"""

import re
from pathlib import Path
from typing import Iterable

from evaluator.shared.path_checks import CPP_LIKE_SUFFIXES, read_text

_INCLUDE_RE = re.compile(r'^\s*#\s*include\s*[<"]([^">]+)[">]', re.MULTILINE)
PatternLike = str | re.Pattern[str]


# 4a. Direct substring / regex signal checks
def regex_matches(pattern: re.Pattern[str], text: str) -> bool:
    """Return whether a compiled regex matches anywhere in the text."""
    return bool(pattern.search(text))


def has_any_substring(needles: Iterable[str], text: str) -> bool:
    """Return whether at least one literal substring is present."""
    return any(needle in text for needle in needles)


def has_all_substrings(needles: Iterable[str], text: str) -> bool:
    """Return whether every literal substring is present."""
    return all(needle in text for needle in needles)


def find_matching_substrings(needles: Iterable[str], text: str) -> list[str]:
    """Return the literal substrings from `needles` that appear in the text."""
    return [needle for needle in needles if needle in text]


def count_matching_substrings(needles: Iterable[str], text: str) -> int:
    """Count how many candidate literal substrings are present."""
    return len(find_matching_substrings(needles, text))


def _compile_pattern(pattern: PatternLike, flags: int = 0) -> re.Pattern[str]:
    if isinstance(pattern, re.Pattern):
        if flags != 0:
            return re.compile(pattern.pattern, pattern.flags | flags)
        return pattern
    return re.compile(pattern, flags)


def find_matching_patterns(
    patterns: Iterable[PatternLike], text: str, *, flags: int = 0
) -> list[PatternLike]:
    """Return the regex patterns that match the text."""
    return [
        pattern for pattern in patterns if _compile_pattern(pattern, flags).search(text)
    ]


def find_missing_patterns(
    patterns: Iterable[PatternLike], text: str, *, flags: int = 0
) -> list[PatternLike]:
    """Return the regex patterns that do not match the text."""
    return [
        pattern
        for pattern in patterns
        if _compile_pattern(pattern, flags).search(text) is None
    ]


def has_any_pattern(patterns: Iterable[PatternLike], text: str, *, flags: int = 0) -> bool:
    """Return whether at least one regex pattern matches the text."""
    return any(_compile_pattern(pattern, flags).search(text) for pattern in patterns)


def count_matching_patterns(
    patterns: Iterable[PatternLike], text: str, *, flags: int = 0
) -> int:
    """Count how many candidate regex patterns match the text."""
    return len(find_matching_patterns(patterns, text, flags=flags))


# 4b. Structure / signal discovery across files
def find_matching_paths(
    pattern: str,
    *paths: Path,
    suffixes: Iterable[str] = CPP_LIKE_SUFFIXES,
    encoding: str = "utf-8",
    errors: str = "replace",
) -> list[Path]:
    """Return files whose contents match a regex pattern.

    Accepts both individual files and directories. Directories are scanned
    recursively and filtered by suffix before contents are searched.
    """
    compiled = re.compile(pattern, re.MULTILINE)
    suffix_set = set(suffixes)
    matches: list[Path] = []

    for path in paths:
        if path.is_dir():
            for file_path in sorted(path.rglob("*")):
                if file_path.suffix not in suffix_set:
                    continue
                text = read_text(
                    file_path, encoding=encoding, errors=errors, missing_ok=False
                )
                if compiled.search(text):
                    matches.append(file_path)
        elif path.is_file():
            text = read_text(path, encoding=encoding, errors=errors, missing_ok=False)
            if compiled.search(text):
                matches.append(path)

    return matches


# 4c. Lightweight source normalization / extraction
def strip_comments(text: str) -> str:
    """Remove C/C++ style comments before signal matching."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    return text


def strip_comments_and_strings(text: str) -> str:
    """Remove string literals and comments to reduce false-positive matches."""
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    text = re.sub(r"'(?:\\.|[^'\\])+'", "''", text)
    return strip_comments(text)


def include_paths(text: str) -> list[str]:
    """Extract `#include` targets from C/C++ source text."""
    return [match.group(1) for match in _INCLUDE_RE.finditer(text)]


def _extract_brace_enclosed_block(text: str, start: int) -> str | None:
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    if depth != 0:
        return None
    return text[start : i - 1]


def find_class_body(text: str, class_name: str) -> str | None:
    """Extract the brace-delimited body of a named class declaration."""
    pattern = re.compile(rf"class\s+{re.escape(class_name)}\b[^{{]*\{{", re.S)
    match = pattern.search(text)
    if not match:
        return None
    return _extract_brace_enclosed_block(text, match.end())


def extract_function_body(text: str, function_name: str) -> str:
    """Extract the brace-delimited body of a named function definition."""
    match = re.search(rf"\b{re.escape(function_name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return ""
    body = _extract_brace_enclosed_block(text, match.end())
    return body if body is not None else ""
