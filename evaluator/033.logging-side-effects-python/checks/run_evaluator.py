#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
from pathlib import Path


def dotted_name(node: ast.AST) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def imported_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_root", required=True)
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    policy_path = case_root / "src" / "loan_policy.py"
    service_path = case_root / "src" / "loan_review_service.py"
    findings: list[str] = []

    for path in (policy_path, service_path):
        if not path.is_file():
            findings.append(f"missing required path: {path.relative_to(case_root)}")
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    try:
        policy_tree = ast.parse(
            policy_path.read_text(encoding="utf-8"), filename=str(policy_path)
        )
        service_tree = ast.parse(
            service_path.read_text(encoding="utf-8"), filename=str(service_path)
        )
    except (OSError, SyntaxError) as exc:
        print(f"FAIL: could not analyze source files: {exc}")
        return 1

    policy_imports = imported_modules(policy_tree)
    forbidden_imports = sorted(
        module
        for module in policy_imports
        if module == "logging" or module.endswith("audit_logger")
    )
    if forbidden_imports:
        findings.append(
            "loan_policy.py must not depend on audit logging: "
            + ", ".join(forbidden_imports)
        )

    policy_functions = [
        node
        for node in policy_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "evaluate_applicant"
    ]
    if len(policy_functions) != 1:
        findings.append("loan_policy.py must define evaluate_applicant() exactly once")
    else:
        function = policy_functions[0]
        parameters = [
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        ]
        if function.args.vararg is not None:
            parameters.append(function.args.vararg)
        if function.args.kwarg is not None:
            parameters.append(function.args.kwarg)
        if len(parameters) != 1 or parameters[0].arg != "applicant":
            findings.append(
                "evaluate_applicant() must accept only the applicant dependency"
            )

    for node in ast.walk(policy_tree):
        if not isinstance(node, ast.Call):
            continue
        called = dotted_name(node.func)
        if called in {"print", "open", "breakpoint"}:
            findings.append(
                f"loan_policy.py must not perform direct I/O: found {called}()"
            )
        elif called and (called == "logging" or called.startswith("logging.")):
            findings.append(
                f"loan_policy.py must not emit logs directly: found {called}()"
            )
        elif isinstance(node.func, ast.Attribute) and node.func.attr in {
            "log",
            "debug",
            "info",
            "warning",
            "error",
            "critical",
            "exception",
        }:
            findings.append(
                f"loan_policy.py must not emit logs directly: found .{node.func.attr}()"
            )

    service_logs = [
        node
        for node in ast.walk(service_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "log"
    ]
    if not service_logs:
        findings.append(
            "loan_review_service.py should localize audit emission with logger.log()"
        )

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print("PASS: logging side effects are isolated from loan policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
