#!/usr/bin/env python3

"""Evaluate declarative source-code rules over files in a case tree.

This is the main content-inspection module for the pipeline system. It scans
source files under configurable roots and evaluates declarative rules such as:
- required or forbidden substrings
- required or forbidden regex patterns
- nested `all_of` / `any_of` / `not` combinations
- file-level global counts like “must appear in at least N files”

Typical use cases:
- banning concrete implementation tokens from abstraction layers
- requiring an API seam or helper call to appear in a source file
- checking that a symbol only appears within an intended ownership boundary
- expressing many former per-case structural Python checks as JSON config

Configuration shape:
- `module_name`: must be `"source_analysis"`
- `name`: human-readable module instance name used in reports
- `root`: optional symbolic root selector such as `case_root`; defaults to
  `"case_root"`
- `scan_roots`: optional list of directories or files to scan; defaults to `src`
- `suffixes`: optional suffix filter for recursive scans
- `exclude_files`: optional filename blacklist
- `exclude_globs`: optional path glob blacklist
- `normalize`: optional normalization mode:
  - `"none"` / omitted
  - `"strip_comments"`
  - `"strip_comments_and_strings"`
- `stop_on_first_match`: optional early-exit flag for faster fail-fast checks
- `rules`: file-level rule list
- `global_rules`: aggregate rules over the scanned file set

Execution behavior:
- resolves scan roots relative to the chosen root
- recursively scans matching files and applies optional normalization
- evaluates each configured rule and reports formatted findings on matches
- supports line-number-aware messages through `{line_no}` / `{location}`
- evaluates aggregate `global_rules` after per-file scanning

This module is the preferred replacement for many custom structural scripts.
When a rule can be represented here cleanly, prefer it over `customized_check`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Mapping

from evaluator.shared.context import EvaluationContext
from evaluator.shared.module.base import EvaluationModule
from evaluator.shared.module.result import ModuleResult
from evaluator.shared.module.path_checks import read_text, scan_files
from evaluator.shared.module.source_analysis import (
    count_matching_patterns,
    count_matching_substrings,
    has_all_substrings,
    has_any_pattern,
    has_any_substring,
    strip_comments,
    strip_comments_and_strings,
)


class SourceAnalysisModule(EvaluationModule):
    module_name = "source_analysis"

    def evaluate(self, context: EvaluationContext) -> ModuleResult:
        """
        Evaluates source files against per-file and aggregate rules, returning pass/fail status and findings.

        Returns:
            ModuleResult: Pass/fail status and rendered findings. Passes if no findings are produced.

        Raises:
            ValueError: If both 'rules' and 'global_rules' are empty in configuration.
        """
        root = self._resolve_root(self.config.get("root", "case_root"), context)
        scan_roots = self.config.get("scan_roots", ["src"])
        suffixes = tuple(self.config.get("suffixes", [".h", ".hpp", ".cc", ".cpp"]))
        exclude_files = set(self.config.get("exclude_files", []))
        exclude_globs = set(self.config.get("exclude_globs", []))
        stop_on_first_match = bool(self.config.get("stop_on_first_match", False))
        rules = self.config.get("rules", [])
        global_rules = self.config.get("global_rules", [])
        if not rules and not global_rules:
            raise ValueError(
                f"Module '{self.name}' requires at least one rule in 'rules' or 'global_rules'"
            )

        resolved_roots = [
            self._resolve_path_value(path, context=context, relative_to=root)
            for path in scan_roots
        ]
        findings: list[str] = []
        scanned_files: list[tuple[Path, str, str]] = []
        for source_file in scan_files(*resolved_roots, suffixes=suffixes):
            rel_path = source_file.relative_to(root).as_posix()
            if source_file.name in exclude_files:
                continue
            if any(source_file.match(glob) for glob in exclude_globs):
                continue
            if any(Path(rel_path).match(glob) for glob in exclude_globs):
                continue

            content = read_text(
                source_file,
                encoding="utf-8",
                errors="replace",
                missing_ok=False,
            )
            content = self._normalize_content(content)
            scanned_files.append((source_file, rel_path, content))
            for rule in rules:
                match_detail = self._match_detail(rule, content)
                if match_detail is not None:
                    findings.append(
                        self._render_message(
                            rule,
                            source_file=source_file,
                            relative_path=rel_path,
                            match_detail=match_detail,
                        )
                    )
                    if stop_on_first_match:
                        return self._base_result(
                            passed=False,
                            findings=findings,
                            details={"root": root.as_posix()},
                        )

        for rule in global_rules:
            matching_files = [
                rel_path
                for source_file, rel_path, content in scanned_files
                if self._match_detail(rule, content) is not None
            ]
            min_matching_files = rule.get("min_matching_files")
            max_matching_files = rule.get("max_matching_files")
            if min_matching_files is not None and len(matching_files) < int(
                min_matching_files
            ):
                findings.append(
                    self._render_global_message(
                        rule,
                        matching_files=matching_files,
                    )
                )
            if max_matching_files is not None and len(matching_files) > int(
                max_matching_files
            ):
                findings.append(
                    self._render_global_message(
                        rule,
                        matching_files=matching_files,
                    )
                )
            if stop_on_first_match and findings:
                return self._base_result(
                    passed=False,
                    findings=findings,
                    details={"root": root.as_posix()},
                )

        return self._base_result(
            passed=not findings,
            findings=findings,
            details={"root": root.as_posix()},
        )

    def _normalize_content(self, content: str) -> str:
        mode = self.config.get("normalize")
        if mode in (None, "", "none"):
            return content
        if mode == "strip_comments":
            return strip_comments(content)
        if mode == "strip_comments_and_strings":
            return strip_comments_and_strings(content)
        raise ValueError(f"Unsupported normalize mode for module '{self.name}': {mode}")

    def _match_detail(
        self, rule: Mapping[str, Any], content: str
    ) -> dict[str, Any] | None:
        all_of = rule.get("all_of", [])
        if all_of:
            child_details = [self._match_detail(child, content) for child in all_of]
            if any(detail is None for detail in child_details):
                return None
            return self._first_location(child_details)

        any_of = rule.get("any_of", [])
        if any_of:
            for child in any_of:
                detail = self._match_detail(child, content)
                if detail is not None:
                    return detail
            return None

        not_rule = rule.get("not")
        if not_rule is not None:
            detail = self._match_detail(not_rule, content)
            if detail is not None:
                return None

        any_substrings = rule.get("any_substrings", [])
        if any_substrings:
            detail = self._first_matching_substring_location(any_substrings, content)
            if detail is None:
                return None
            return detail

        all_substrings = rule.get("all_substrings", [])
        if all_substrings:
            details = [
                self._first_matching_substring_location([needle], content)
                for needle in all_substrings
            ]
            if any(detail is None for detail in details):
                return None
            return self._first_location(details)

        any_patterns = rule.get("any_patterns", [])
        if any_patterns:
            detail = self._first_matching_pattern_location(any_patterns, content)
            if detail is None:
                return None
            return detail

        all_patterns = rule.get("all_patterns", [])
        if all_patterns:
            details = [
                self._first_matching_pattern_location([pattern], content)
                for pattern in all_patterns
            ]
            if any(detail is None for detail in details):
                return None
            return self._first_location(details)

        for threshold in rule.get("substring_hit_thresholds", []):
            needles = threshold.get("needles", [])
            at_least = int(threshold.get("at_least", 1))
            if count_matching_substrings(needles, content) < at_least:
                return None

        for threshold in rule.get("pattern_hit_thresholds", []):
            patterns = threshold.get("patterns", [])
            at_least = int(threshold.get("at_least", 1))
            flags = _parse_regex_flags(threshold.get("flags", []))
            if count_matching_patterns(patterns, content, flags=flags) < at_least:
                return None

        return {}

    def _render_message(
        self,
        rule: Mapping[str, Any],
        *,
        source_file: Path,
        relative_path: str,
        match_detail: Mapping[str, Any] | None = None,
    ) -> str:
        template = (
            rule.get("message") or "Source analysis rule '{rule_id}' matched in {path}"
        )
        line_no = match_detail.get("line_no") if match_detail else None
        location = f"{relative_path}:{line_no}" if line_no else relative_path
        return template.format(
            rule_id=rule.get("id", "unnamed_rule"),
            path=source_file.as_posix(),
            relative_path=relative_path,
            line_no=line_no if line_no is not None else "",
            location=location,
            filename=source_file.name,
        )

    def _render_global_message(
        self,
        rule: Mapping[str, Any],
        *,
        matching_files: list[str],
    ) -> str:
        template = (
            rule.get("message") or "Global source analysis rule '{rule_id}' matched"
        )
        return template.format(
            rule_id=rule.get("id", "unnamed_rule"),
            matching_file_count=len(matching_files),
            matching_files=", ".join(matching_files),
        )

    def _first_matching_substring_location(
        self, needles: Iterable[str], content: str
    ) -> dict[str, Any] | None:
        first_index: int | None = None
        for needle in needles:
            index = content.find(needle)
            if index == -1:
                continue
            if first_index is None or index < first_index:
                first_index = index
        if first_index is None:
            return None
        return {"line_no": _line_no_at(content, first_index)}

    def _first_matching_pattern_location(
        self, patterns: Iterable[str], content: str
    ) -> dict[str, Any] | None:
        first_index: int | None = None
        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match is None:
                continue
            index = match.start()
            if first_index is None or index < first_index:
                first_index = index
        if first_index is None:
            return None
        return {"line_no": _line_no_at(content, first_index)}

    def _first_location(
        self, details: Iterable[dict[str, Any] | None]
    ) -> dict[str, Any]:
        line_numbers = [
            detail.get("line_no")
            for detail in details
            if detail is not None and detail.get("line_no") is not None
        ]
        if not line_numbers:
            return {}
        return {"line_no": min(line_numbers)}


def _parse_regex_flags(values: Iterable[str]) -> int:
    flags = 0
    for value in values:
        try:
            flags |= getattr(re, value)
        except AttributeError as exc:
            raise ValueError(f"Unsupported regex flag: {value}") from exc
    return flags


def _line_no_at(content: str, index: int) -> int:
    return content.count("\n", 0, index) + 1
