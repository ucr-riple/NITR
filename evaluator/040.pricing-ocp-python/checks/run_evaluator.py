#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from pathlib import Path

COUPON_TERMS = ("coupon", "promo")
KNOWN_RULE_VALUES = {
    "SAVE5",
    "SAVE10P",
    "ITEMS_20OFF",
    "MEMBER_10P",
    "COUPON_SAVE5",
    "COUPON_SAVE10P",
}


def local_calls(function: ast.AST, names: set[str]) -> set[str]:
    calls: set[str] = set()
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in names:
                calls.add(node.func.id)
    return calls


def references_coupon(node: ast.AST) -> bool:
    for child in ast.walk(node):
        name: str | None = None
        if isinstance(child, ast.Name):
            name = child.id
        elif isinstance(child, ast.Attribute):
            name = child.attr
        if name and any(term in name.lower() for term in COUPON_TERMS):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    core_path = case_root / "src" / "pricing.py"
    if not core_path.is_file():
        print("FAIL: missing required path: src/pricing.py")
        return 1

    try:
        tree = ast.parse(
            core_path.read_text(encoding="utf-8"), filename=str(core_path)
        )
    except (OSError, SyntaxError) as exc:
        print(f"FAIL: could not analyze src/pricing.py: {exc}")
        return 1

    findings: list[str] = []
    module_functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    functions = [
        node
        for name, node in module_functions.items()
        if name == "compute_final_price"
    ]
    if len(functions) != 1:
        findings.append("pricing core must define compute_final_price() exactly once")
    else:
        reachable: dict[str, ast.AST] = {}
        pending = ["compute_final_price"]
        while pending:
            name = pending.pop()
            if name in reachable:
                continue
            function = module_functions[name]
            reachable[name] = function
            pending.extend(
                local_calls(function, set(module_functions)) - set(reachable)
            )

        for function_name, function in reachable.items():
            for node in ast.walk(function):
                if (
                    isinstance(node, (ast.If, ast.IfExp))
                    and references_coupon(node.test)
                ):
                    findings.append(
                        f"{function_name}() must not branch on coupon or promo values"
                    )
                if isinstance(node, ast.Match) and references_coupon(node.subject):
                    findings.append(
                        f"{function_name}() must not dispatch on coupon or promo values"
                    )
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and node.value in KNOWN_RULE_VALUES
                ):
                    findings.append(
                        f"pricing core path contains rule-specific value: {node.value}"
                    )

        core = reachable["compute_final_price"]
        creates_rules = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_all"
            for function in reachable.values()
            for node in ast.walk(function)
        )
        if not creates_rules:
            findings.append(
                "compute_final_price() must obtain rules through RuleRegistry.create_all()"
            )

    if findings:
        for finding in dict.fromkeys(findings):
            print(f"FAIL: {finding}")
        return 1

    print("PASS: pricing core remains open to registry-based rule extensions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
