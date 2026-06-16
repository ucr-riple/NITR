#!/usr/bin/env python3

"""Source-analysis evaluation module."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Mapping

from evaluator.shared.context import EvaluationContext
from evaluator.shared.module.base import EvaluationModule
from evaluator.shared.module.result import ModuleResult
from evaluator.shared.module.path_checks import scan_files
from evaluator.shared.module.source_analysis import (
    count_matching_patterns,
    count_matching_substrings,
    has_all_substrings,
    has_any_pattern,
    has_any_substring,
)


class SourceAnalysisModule(EvaluationModule):
    module_name = "source_analysis"

    def evaluate(self, context: EvaluationContext) -> ModuleResult:
        root = self._resolve_root(self.config.get("root", "case_root"), context)
        scan_roots = self.config.get("scan_roots", ["src"])
        suffixes = tuple(self.config.get("suffixes", [".h", ".hpp", ".cc", ".cpp"]))
        exclude_files = set(self.config.get("exclude_files", []))
        exclude_globs = set(self.config.get("exclude_globs", []))
        stop_on_first_match = bool(self.config.get("stop_on_first_match", False))
        rules = self.config.get("rules", [])
        global_rules = self.config.get("global_rules", [])
        if not rules and not global_rules:
            raise ValueError(f"Module '{self.name}' requires a non-empty 'rules' list")

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

            content = source_file.read_text(encoding="utf-8", errors="replace")
            scanned_files.append((source_file, rel_path, content))
            for rule in rules:
                if self._rule_matches(rule, content):
                    findings.append(
                        self._render_message(
                            rule,
                            source_file=source_file,
                            relative_path=rel_path,
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
                if self._rule_matches(rule, content)
            ]
            min_matching_files = rule.get("min_matching_files")
            max_matching_files = rule.get("max_matching_files")
            if (
                min_matching_files is not None
                and len(matching_files) < int(min_matching_files)
            ):
                findings.append(
                    self._render_global_message(
                        rule,
                        matching_files=matching_files,
                    )
                )
            if (
                max_matching_files is not None
                and len(matching_files) > int(max_matching_files)
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

    def _rule_matches(self, rule: Mapping[str, Any], content: str) -> bool:
        all_of = rule.get("all_of", [])
        if all_of and not all(self._rule_matches(child, content) for child in all_of):
            return False

        any_of = rule.get("any_of", [])
        if any_of and not any(self._rule_matches(child, content) for child in any_of):
            return False

        not_rule = rule.get("not")
        if not_rule is not None and self._rule_matches(not_rule, content):
            return False

        any_substrings = rule.get("any_substrings", [])
        if any_substrings and not has_any_substring(any_substrings, content):
            return False

        all_substrings = rule.get("all_substrings", [])
        if all_substrings and not has_all_substrings(all_substrings, content):
            return False

        any_patterns = rule.get("any_patterns", [])
        if any_patterns and not has_any_pattern(any_patterns, content):
            return False

        all_patterns = rule.get("all_patterns", [])
        if all_patterns:
            compiled = [re.compile(pattern) for pattern in all_patterns]
            if not all(pattern.search(content) for pattern in compiled):
                return False

        for threshold in rule.get("substring_hit_thresholds", []):
            needles = threshold.get("needles", [])
            at_least = int(threshold.get("at_least", 1))
            if count_matching_substrings(needles, content) < at_least:
                return False

        for threshold in rule.get("pattern_hit_thresholds", []):
            patterns = threshold.get("patterns", [])
            at_least = int(threshold.get("at_least", 1))
            flags = _parse_regex_flags(threshold.get("flags", []))
            if count_matching_patterns(patterns, content, flags=flags) < at_least:
                return False

        return True

    def _render_message(
        self,
        rule: Mapping[str, Any],
        *,
        source_file: Path,
        relative_path: str,
    ) -> str:
        template = (
            rule.get("message")
            or "Source analysis rule '{rule_id}' matched in {path}"
        )
        return template.format(
            rule_id=rule.get("id", "unnamed_rule"),
            path=source_file.as_posix(),
            relative_path=relative_path,
            filename=source_file.name,
        )

    def _render_global_message(
        self,
        rule: Mapping[str, Any],
        *,
        matching_files: list[str],
    ) -> str:
        template = rule.get("message") or "Global source analysis rule '{rule_id}' matched"
        return template.format(
            rule_id=rule.get("id", "unnamed_rule"),
            matching_file_count=len(matching_files),
            matching_files=", ".join(matching_files),
        )


def _parse_regex_flags(values: Iterable[str]) -> int:
    flags = 0
    for value in values:
        try:
            flags |= getattr(re, value)
        except AttributeError as exc:
            raise ValueError(f"Unsupported regex flag: {value}") from exc
    return flags
