#!/usr/bin/env python3

"""Structural check for case 024: substitutability under interface evolution.

Verifies that the agent evolved the abstract MetricRecorder base to admit
the new buffered implementation while preserving substitutability for the
existing console implementation.

These are semantic, type-relationship-level assertions. There is no
function-name blacklist; the check verifies the architecture, not syntax.
"""

import argparse
import re
from pathlib import Path

from evaluator.shared.path_checks import (
    case_root_from_script,
    read_text,
    scan_files,
)
from evaluator.shared.check_output import emit_check_result
from evaluator.shared.source_analysis import (
    find_class_body,
    find_matching_patterns,
    has_any_pattern,
    strip_comments,
)



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


def has_virtual_method_matching(class_body: str, name_pattern: str) -> bool:
    """Check if class body contains a virtual method matching the given name pattern.

    Matches both pure virtual (= 0) and virtual with default implementation.
    Excludes destructors.
    """
    # Match virtual methods: virtual ... MethodName(...) ... [= 0] ; or { ... }
    # This covers:
    # - virtual void Flush() = 0;  (pure virtual)
    # - virtual void Flush();      (declaration, impl in .cc)
    # - virtual void Flush() {}    (inline default implementation)
    pattern = re.compile(
        rf"virtual\s+[^;{{}}]*?\b({name_pattern})\s*\([^;{{}}]*\)\s*(?:const\s*)?(?:noexcept\s*)?(?:=\s*0\s*)?(?:;|\s*\{{)",
        re.S,
    )
    for m in pattern.finditer(class_body):
        name = m.group(1)
        if name.startswith("~"):
            continue
        return True
    return False


def main() -> int:

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case_root",
        type=Path,
        default=case_root_from_script(__file__),
    )
    args = parser.parse_args()

    case_root = args.case_root.resolve()
    src_dir = case_root / "src"
    failures: list[str] = []

    recorder_h = read_text(src_dir / "metric_recorder.h")
    if not recorder_h:
        return emit_check_result(
            passed=False, findings=["metric_recorder.h is missing."]
        )

    recorder_h_clean = strip_comments(recorder_h)
    recorder_body = find_class_body(recorder_h_clean, "MetricRecorder")
    if recorder_body is None:
        failures.append(
            "metric_recorder.h: class MetricRecorder declaration not found."
        )
    else:
        # Assertion 1: the abstract base must admit a polymorphic visibility-trigger
        # (e.g. Flush) alongside Record. This can be pure virtual (= 0) or virtual
        # with a default implementation (e.g. empty body for immediate-write recorders).
        # The key is that it must be callable through the base class reference.
        #
        # If the agent added the visibility-trigger only on the buffered subclass,
        # consumers would be forced to downcast, breaking substitutability.

        # Check for Record (must exist)
        has_record = has_virtual_method_matching(recorder_body, r"Record")
        if not has_record:
            failures.append(
                "metric_recorder.h: MetricRecorder must declare Record as a "
                "virtual member."
            )

        # Check for visibility-trigger (Flush, Commit, Sync, etc.)
        # Common names for visibility triggers
        visibility_trigger_names = [
            r"Flush",
            r"Commit",
            r"Sync",
            r"MakeVisible",
            r"Publish",
            r"Drain",
            r"Write",
        ]
        has_visibility_trigger = any(
            has_virtual_method_matching(recorder_body, name)
            for name in visibility_trigger_names
        )

        if not has_visibility_trigger:
            failures.append(
                "metric_recorder.h: the abstract MetricRecorder base must admit "
                "a polymorphic visibility-trigger (e.g. Flush, Commit, Sync) "
                "alongside Record. This can be pure virtual or virtual with default "
                "implementation, but must be callable through the base class "
                "reference so consumers can trigger visibility on any recorder "
                "without downcasting."
            )

        # Sanity: Record must still be a virtual member of the base.
        if not re.search(r"virtual\s+[^;{}]*\bRecord\s*\(", recorder_body):
            failures.append(
                "metric_recorder.h: MetricRecorder must keep Record as a "
                "virtual member."
            )

    # Assertion 2: a buffered MetricRecorder subclass must exist.
    buffered_class_match: tuple[Path, str] | None = None
    for path in scan_files(src_dir, suffixes=(".h",)):
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

    # Assertion 3: the buffered recorder must override Record and provide
    # a real flush implementation. At minimum, Record must be overridden.
    # If the base visibility-trigger is pure virtual, it must also be overridden.
    # If the base visibility-trigger has a default implementation, the buffered
    # recorder should still override it to provide actual flush logic (but this
    # is verified by functional tests, not structural checks).
    if buffered_class_match is not None:
        bpath, bname = buffered_class_match
        btext = strip_comments(bpath.read_text(encoding="utf-8"))
        bbody = find_class_body(btext, bname) or ""

        # Check that Record is overridden
        has_record_override = re.search(
            r"\bRecord\s*\([^)]*\)[^;{]*\boverride\b", bbody
        )
        if not has_record_override:
            failures.append(
                f"{bpath.name}: {bname} must override Record to provide "
                "buffered recording logic."
            )

    # Assertion 4: the existing immediate-write recorder must override Record.
    # The visibility-trigger can be inherited from the base if the base provides
    # a default implementation (e.g. virtual void Flush() {}), or must be
    # overridden if the base declares it pure virtual.
    #
    # We already verified in Assertion 1 that the base declares a polymorphic
    # visibility-trigger, so we just need to ensure ConsoleMetricRecorder can
    # call it (either by overriding or inheriting). Since C++ inheritance
    # provides this automatically, we only verify that Record is overridden.
    console_h = read_text(src_dir / "console_metric_recorder.h")
    console_cc = read_text(src_dir / "console_metric_recorder.cc")
    console_combined = strip_comments(console_h + "\n" + console_cc)
    console_body = (
        find_class_body(strip_comments(console_h), "ConsoleMetricRecorder") or ""
    )

    # Check that Record is overridden
    has_console_record_override = re.search(
        r"\bRecord\s*\([^)]*\)[^;{]*\boverride\b", console_body
    )
    if not has_console_record_override:
        failures.append(
            "console_metric_recorder.h: ConsoleMetricRecorder must override "
            "Record to provide immediate-write recording logic."
        )

    # Assertion 5: MetricCollector must operate through the abstract
    # MetricRecorder reference. It must not name any concrete recorder
    # type in its source files (excluding #include lines, which are
    # implementation-detail noise that does not constitute a dependency
    # in the type system).
    collector_h = read_text(src_dir / "metric_collector.h")
    collector_cc = read_text(src_dir / "metric_collector.cc")
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
        if has_any_pattern([rf"\b{re.escape(concrete)}\b"], non_include_lines):
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

    # Assertion 7: MetricCollector must not use capability branching
    # (e.g. if (recorder_.IsBuffered()) { ... }). The SPEC explicitly
    # lists this as an undesirable direction. The visibility-trigger
    # should be unconditionally callable on any recorder implementation.
    capability_patterns = [
        r"\bIsBuffered\s*\(",
        r"\bSupportsFlush\s*\(",
        r"\bCanFlush\s*\(",
        r"\bHasBuffer\s*\(",
        r"\bNeedsFlush\s*\(",
        r"\bRequiresFlush\s*\(",
        # Also catch conditional calls to flush-like methods
        r"if\s*\([^)]*\.(Flush|Commit|Sync|MakeVisible|Publish|Drain)\s*\(",
    ]
    matching_capability_patterns = find_matching_patterns(
        capability_patterns, collector_combined, flags=re.IGNORECASE
    )
    if matching_capability_patterns:
        failures.append(
            "metric_collector contains capability branching "
            f"(pattern: {matching_capability_patterns[0]!r}). The checkpoint operation must "
            "unconditionally invoke the polymorphic visibility-trigger "
            "on the abstract recorder reference. Capability predicates "
            "(e.g. IsBuffered, SupportsFlush) break substitutability "
            "by making the caller aware of implementation details."
        )

    return emit_check_result(passed=not failures, findings=failures)


if __name__ == "__main__":
    raise SystemExit(main())
