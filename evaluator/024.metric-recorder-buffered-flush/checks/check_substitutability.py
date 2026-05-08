#!/usr/bin/env python3
"""Structural check for case 024: substitutability under interface evolution.

Verifies that the agent evolved the abstract MetricRecorder base to admit
the new buffered implementation while preserving substitutability for the
existing console implementation.

These are semantic, type-relationship-level assertions. There is no
function-name blacklist; the check verifies the architecture, not syntax.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CASE_NAME = Path(__file__).resolve().parents[1].name
SRC_DIR = REPO_ROOT / "cases" / CASE_NAME / "src"


def read(name: str) -> str:
    p = SRC_DIR / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def all_src_headers() -> list[Path]:
    return sorted(p for p in SRC_DIR.rglob("*.h"))


def all_src_files() -> list[Path]:
    return sorted(p for p in SRC_DIR.rglob("*") if p.suffix in {".h", ".cc"})


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    return text


def count_pure_virtual_methods(class_body: str) -> int:
    """Count pure-virtual non-destructor methods inside a class body."""
    pattern = re.compile(
        r"virtual\s+[^;{}]*?\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*(?:const\s*)?(?:noexcept\s*)?=\s*0\s*;",
        re.S,
    )
    count = 0
    for m in pattern.finditer(class_body):
        name = m.group(1)
        if name.startswith("~"):
            continue
        count += 1
    return count


def find_class_body(source: str, class_name: str) -> str | None:
    """Return the body of a class declaration, or None if not found."""
    # Match class declaration up through the matching brace.
    pattern = re.compile(
        rf"class\s+{re.escape(class_name)}\b[^{{]*\{{",
        re.S,
    )
    m = pattern.search(source)
    if not m:
        return None
    start = m.end()
    depth = 1
    i = start
    while i < len(source) and depth > 0:
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
        i += 1
    if depth != 0:
        return None
    return source[start : i - 1]


def main() -> int:
    failures: list[str] = []

    recorder_h = read("metric_recorder.h")
    if not recorder_h:
        print("[STRUCTURE FAIL] metric_recorder.h is missing.")
        return 1

    recorder_h_clean = strip_comments(recorder_h)
    recorder_body = find_class_body(recorder_h_clean, "MetricRecorder")
    if recorder_body is None:
        failures.append(
            "metric_recorder.h: class MetricRecorder declaration not found."
        )
    else:
        # Assertion 1: the abstract base must declare AT LEAST 2 pure-virtual
        # methods (Record + a polymorphic visibility-trigger). If the agent
        # added the visibility-trigger only on the buffered subclass, the
        # base will have only 1 pure-virtual and consumers must downcast.
        pure_virtual_count = count_pure_virtual_methods(recorder_body)
        if pure_virtual_count < 2:
            failures.append(
                "metric_recorder.h: the abstract MetricRecorder base has fewer "
                "than 2 pure-virtual methods (found "
                f"{pure_virtual_count}). The base must admit a polymorphic "
                "visibility-trigger (e.g. Flush) alongside Record so consumers "
                "can flush any recorder through the abstract reference."
            )

        # Sanity: Record must still be a virtual member of the base.
        if not re.search(r"virtual\s+[^;{}]*\bRecord\s*\(", recorder_body):
            failures.append(
                "metric_recorder.h: MetricRecorder must keep Record as a "
                "virtual member."
            )

    # Assertion 2: a buffered MetricRecorder subclass must exist.
    buffered_class_match: tuple[Path, str] | None = None
    for path in all_src_headers():
        text = strip_comments(path.read_text(encoding="utf-8"))
        m = re.search(
            r"class\s+(\w+)\s*:\s*public\s+MetricRecorder\b",
            text,
        )
        if not m:
            continue
        name = m.group(1)
        if name == "ConsoleMetricRecorder":
            continue
        # Heuristic: prefer a class whose name signals buffering.
        buffered_class_match = (path, name)
        if "buffer" in name.lower() or "buffer" in path.name.lower():
            break

    if buffered_class_match is None:
        failures.append(
            "no new MetricRecorder subclass found alongside ConsoleMetricRecorder. "
            "The new buffered implementation must derive from MetricRecorder so it "
            "is substitutable wherever the console recorder is used today."
        )

    # Assertion 3: the buffered recorder must override BOTH Record and the
    # polymorphic visibility-trigger (i.e. the class body must contain at
    # least 2 'override' tokens on member functions).
    if buffered_class_match is not None:
        bpath, bname = buffered_class_match
        btext = strip_comments(bpath.read_text(encoding="utf-8"))
        bbody = find_class_body(btext, bname) or ""
        override_count = len(re.findall(r"\boverride\b", bbody))
        if override_count < 2:
            failures.append(
                f"{bpath.name}: {bname} declares {override_count} 'override' "
                "method(s); it must override BOTH Record AND the polymorphic "
                "visibility-trigger declared on the abstract base. If only "
                "one is overridden, the abstraction is incomplete."
            )

    # Assertion 4: the existing immediate-write recorder must also override
    # the polymorphic visibility-trigger. A no-op body is fine. Without
    # this, the agent has likely added the visibility-trigger only on the
    # buffered impl, breaking substitutability.
    console_h = read("console_metric_recorder.h")
    console_cc = read("console_metric_recorder.cc")
    console_combined = strip_comments(console_h + "\n" + console_cc)
    console_body = find_class_body(strip_comments(console_h), "ConsoleMetricRecorder") or ""
    console_override_count = len(re.findall(r"\boverride\b", console_body))
    if console_override_count < 2:
        failures.append(
            "console_metric_recorder.h: ConsoleMetricRecorder declares "
            f"{console_override_count} 'override' method(s); it must override "
            "BOTH the abstract base's pure-virtual methods. If the polymorphic "
            "visibility-trigger lives only on the buffered subclass, "
            "consumers are forced to downcast and substitutability is lost."
        )

    # Assertion 5: MetricCollector must operate through the abstract
    # MetricRecorder reference. It must not name any concrete recorder
    # type in its source files (excluding #include lines, which are
    # implementation-detail noise that does not constitute a dependency
    # in the type system).
    collector_h = read("metric_collector.h")
    collector_cc = read("metric_collector.cc")
    collector_combined = strip_comments(collector_h + "\n" + collector_cc)
    non_include_lines = "\n".join(
        line
        for line in collector_combined.splitlines()
        if not re.match(r"^\s*#\s*include", line)
    )
    concrete_types = ["ConsoleMetricRecorder"]
    if buffered_class_match is not None:
        concrete_types.append(buffered_class_match[1])
    for concrete in concrete_types:
        if re.search(rf"\b{re.escape(concrete)}\b", non_include_lines):
            failures.append(
                f"metric_collector.{{h,cc}} references concrete recorder type "
                f"{concrete!r}. MetricCollector must operate through the "
                "abstract MetricRecorder reference; the checkpoint operation "
                "must not be coupled to a specific recorder implementation."
            )

    # Assertion 6: MetricCollector must not use dynamic_cast to reach a
    # concrete recorder. The polymorphic visibility-trigger should be
    # callable directly through the abstract reference.
    if "dynamic_cast" in collector_combined:
        failures.append(
            "metric_collector uses dynamic_cast. The checkpoint operation "
            "must invoke the polymorphic visibility-trigger directly through "
            "the abstract MetricRecorder reference, without runtime type "
            "discovery."
        )

    if failures:
        print("Substitutability check failed:")
        for f in failures:
            print(f"[STRUCTURE FAIL] {f}")
        return 1

    print("Substitutability check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
