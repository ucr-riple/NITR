#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_method_body(text: str, method_name: str) -> str:
    match = re.search(
        rf"(?ms)^    def {re.escape(method_name)}\(.*?\)[^\n]*:\n"
        r"((?:^(?:        |\t).*\n?|^\n)*)",
        text,
    )
    return match.group(1) if match else ""


def find_assigned_self_attrs(body: str) -> set[str]:
    return set(re.findall(r"\bself\.(\w+)\s*=", body))


def find_read_self_attrs(body: str) -> set[str]:
    attrs = set(re.findall(r"\bself\.(\w+)\b", body))
    return {attr for attr in attrs if f"self.{attr} =" not in body}


def has_lifecycle_control_flow(text: str) -> bool:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if not re.match(r"(if|for|while)\b.*:\s*$", stripped):
            continue

        lookahead = index + 1
        while lookahead < len(lines):
            next_line = lines[lookahead]
            next_stripped = next_line.lstrip()
            next_indent = len(next_line) - len(next_stripped)

            if not next_stripped:
                lookahead += 1
                continue
            if next_indent <= indent:
                break
            if re.search(
                r"\b(register_snapshot|activate_snapshot|reset_active_snapshot)\s*\(",
                next_stripped,
            ):
                return True
            lookahead += 1

    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root)
    src_dir = case_root / "src"
    app_main = case_root / "app" / "main.py"

    required_paths = [
        src_dir / "snapshot.py",
        src_dir / "query_result.py",
        src_dir / "snapshot_store.py",
        src_dir / "query_service.py",
    ]

    findings: list[str] = []
    for path in required_paths:
        if not path.is_file():
            findings.append(f"missing required path: {path.relative_to(case_root)}")

    for path in src_dir.glob("*.py"):
        text = read_text(path)
        if re.search(r"^(ACTIVE_|GLOBAL_ACTIVE_|G_ACTIVE_)\w+\s*=", text, re.MULTILINE):
            findings.append(
                f"{path.relative_to(case_root)}: detected module-level mutable active-state global."
            )

    tracker_hits = 0
    for path in [src_dir / "snapshot_store.py", src_dir / "query_service.py"]:
        if not path.is_file():
            continue
        text = read_text(path)
        if re.search(
            r"self\._(active_version|has_active|current_active|active_snapshot)\b",
            text,
        ):
            tracker_hits += 1
    if tracker_hits > 1:
        findings.append("Multiple core modules appear to maintain writable active-state trackers.")

    query_service_path = src_dir / "query_service.py"
    if query_service_path.is_file():
        query_text = read_text(query_service_path)
        if re.search(r"self\._snapshot(s)?\b|self\._data\b", query_text):
            findings.append(
                "QueryService appears to own mutable snapshot payload/state instead of depending on SnapshotStore."
            )

        init_body = extract_method_body(query_text, "__init__")
        lookup_body = extract_method_body(query_text, "lookup")
        receiver_attrs = set(re.findall(r"\bself\.(\w+)\.\w+\s*\(", lookup_body))
        extra_init_attrs = find_assigned_self_attrs(init_body) - receiver_attrs
        lookup_read_attrs = find_read_self_attrs(lookup_body) - receiver_attrs
        live_resolution = bool(
            re.search(r"\bself\.\w+\.get_active_snapshot\(", lookup_body)
        )

        binder_assigned_attrs: set[str] = set()
        for method_name in re.findall(r"^    def (\w+)\(", query_text, re.MULTILINE):
            if method_name in {"__init__", "lookup"}:
                continue
            if not re.search(r"(bind|refresh|cache|set_active|load_active)", method_name):
                continue
            method_body = extract_method_body(query_text, method_name)
            binder_assigned_attrs.update(find_assigned_self_attrs(method_body) - receiver_attrs)

        suspect_cached_attrs = (extra_init_attrs | binder_assigned_attrs) & lookup_read_attrs
        stale_alias_signals = 0
        if extra_init_attrs:
            stale_alias_signals += 1
        if binder_assigned_attrs:
            stale_alias_signals += 1
        if suspect_cached_attrs and not live_resolution:
            stale_alias_signals += 1

        if stale_alias_signals >= 2 and suspect_cached_attrs:
            attrs_text = ", ".join(sorted(suspect_cached_attrs))
            findings.append(
                "QueryService appears to retain a bound active snapshot alias instead of "
                f"resolving through the lifecycle owner. Suspicious cached attrs: {attrs_text}."
            )

    if app_main.is_file():
        main_text = read_text(app_main)
        if has_lifecycle_control_flow(main_text):
            findings.append(
                "Lifecycle control flow appears in app/main.py; keep it in core src ownership."
            )

    for path in src_dir.glob("*.py"):
        if path.name == "snapshot_store.py":
            continue
        text = read_text(path)
        if re.search(r"\breset_active_snapshot\s*\(", text):
            findings.append("reset_active_snapshot logic appears outside snapshot_store.py.")
            break

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: structural checks succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
