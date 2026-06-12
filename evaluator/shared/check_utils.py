from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, NoReturn


CPP_LIKE_SUFFIXES = (".h", ".hpp", ".hh", ".cc", ".cpp", ".cxx")
_INCLUDE_RE = re.compile(r'^\s*#\s*include\s*[<"]([^">]+)[">]', re.MULTILINE)
PatternLike = str | re.Pattern[str]


def repo_root_from_script(script_path: str | Path) -> Path:
    return Path(script_path).resolve().parents[3]


def case_name_from_script(script_path: str | Path) -> str:
    return Path(script_path).resolve().parents[1].name


def case_root_from_script(script_path: str | Path) -> Path:
    return repo_root_from_script(script_path) / "cases" / case_name_from_script(
        script_path
    )


def evaluator_root_from_script(script_path: str | Path) -> Path:
    return repo_root_from_script(script_path) / "evaluator" / case_name_from_script(
        script_path
    )


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def read_text(
    path: Path,
    *,
    encoding: str = "utf-8",
    errors: str | None = None,
    missing_ok: bool = True,
) -> str:
    if missing_ok and not path.exists():
        return ""
    kwargs = {"encoding": encoding}
    if errors is not None:
        kwargs["errors"] = errors
    return path.read_text(**kwargs)


def fail_message(message: str) -> int:
    print(message)
    return 1


def die_message(message: str) -> NoReturn:
    print(message)
    raise SystemExit(1)


def scan_files(*roots: Path, suffixes: Iterable[str] = CPP_LIKE_SUFFIXES) -> list[Path]:
    if not roots:
        return []
    suffix_set = set(suffixes)
    return sorted(
        {
            path
            for root in roots
            for path in root.rglob("*")
            if path.is_file() and path.suffix in suffix_set
        }
    )


def regex_matches(pattern: re.Pattern[str], text: str) -> bool:
    return bool(pattern.search(text))


def has_any_substring(needles: Iterable[str], text: str) -> bool:
    return any(needle in text for needle in needles)


def has_all_substrings(needles: Iterable[str], text: str) -> bool:
    return all(needle in text for needle in needles)


def count_matching_substrings(needles: Iterable[str], text: str) -> int:
    return sum(needle in text for needle in needles)


def _compile_pattern(pattern: PatternLike, flags: int = 0) -> re.Pattern[str]:
    if isinstance(pattern, re.Pattern):
        if flags != 0:
            return re.compile(pattern.pattern, pattern.flags | flags)
        return pattern
    return re.compile(pattern, flags)


def find_matching_patterns(
    patterns: Iterable[PatternLike], text: str, *, flags: int = 0
) -> list[PatternLike]:
    return [pattern for pattern in patterns if _compile_pattern(pattern, flags).search(text)]


def find_missing_patterns(
    patterns: Iterable[PatternLike], text: str, *, flags: int = 0
) -> list[PatternLike]:
    return [
        pattern for pattern in patterns if _compile_pattern(pattern, flags).search(text) is None
    ]


def has_any_pattern(patterns: Iterable[PatternLike], text: str, *, flags: int = 0) -> bool:
    return any(_compile_pattern(pattern, flags).search(text) for pattern in patterns)


def count_matching_patterns(
    patterns: Iterable[PatternLike], text: str, *, flags: int = 0
) -> int:
    return len(find_matching_patterns(patterns, text, flags=flags))


def find_matching_paths(
    pattern: str,
    *paths: Path,
    suffixes: Iterable[str] = (".h", ".cc"),
    encoding: str = "utf-8",
    errors: str = "replace",
) -> list[Path]:
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


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    return text


def strip_comments_and_strings(text: str) -> str:
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    text = re.sub(r"'(?:\\.|[^'\\])+'", "''", text)
    return strip_comments(text)


def include_paths(text: str) -> list[str]:
    return [match.group(1) for match in _INCLUDE_RE.finditer(text)]


def find_class_body(text: str, class_name: str) -> str | None:
    pattern = re.compile(rf"class\s+{re.escape(class_name)}\b[^{{]*\{{", re.S)
    match = pattern.search(text)
    if not match:
        return None

    start = match.end()
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


def extract_function_body(text: str, function_name: str) -> str:
    match = re.search(rf"\b{re.escape(function_name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return ""

    start = match.end()
    depth = 1
    i = start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i]
        i += 1
    return ""
