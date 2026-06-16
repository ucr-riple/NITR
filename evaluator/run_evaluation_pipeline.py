#!/usr/bin/env python3

"""Run config-driven evaluator modules and emit a single JSON payload."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

_module_repo_root = Path(__file__).resolve().parents[1]
if _module_repo_root.as_posix() not in sys.path:
    sys.path.insert(0, _module_repo_root.as_posix())

from evaluator.shared.check_output import CHECK_FAILED, CHECK_PASSED
from evaluator.shared.context import DefaultEvaluationContext
from evaluator.shared.module import module_from_config


def _load_config(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise SystemExit(
                "YAML config requested but PyYAML is not installed. Use JSON or install PyYAML."
            ) from exc
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise SystemExit("Top-level YAML config must be a mapping/object.")
        return loaded
    raise SystemExit(f"Unsupported config suffix for {path}. Use .json, .yaml, or .yml.")


def _resolve_override(
    explicit: str | None,
    config: dict[str, Any],
    key: str,
    *,
    default: Path | None = None,
    base_dir: Path,
) -> Path | None:
    value = explicit if explicit is not None else config.get(key)
    if value is None:
        return default
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate.resolve()
    return (base_dir / candidate).resolve()


def _coerce_variable_value(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return value


def _parse_cli_variables(entries: list[str]) -> dict[str, Any]:
    variables: dict[str, Any] = {}
    for entry in entries:
        if "=" not in entry:
            raise SystemExit(f"Invalid --set value '{entry}'. Expected key=value.")
        key, raw_value = entry.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"Invalid --set value '{entry}'. Key cannot be empty.")
        variables[key] = _coerce_variable_value(raw_value.strip())
    return variables


def _parse_path_overrides(entries: list[str]) -> dict[str, str]:
    allowed_keys = {"case_root", "baseline_case_root", "build_dir"}
    overrides: dict[str, str] = {}
    for entry in entries:
        if "=" not in entry:
            raise SystemExit(
                f"Invalid --override value '{entry}'. Expected key=path."
            )
        key, raw_value = entry.split("=", 1)
        key = key.strip()
        value = raw_value.strip()
        if key not in allowed_keys:
            allowed = ", ".join(sorted(allowed_keys))
            raise SystemExit(
                f"Invalid --override key '{key}'. Allowed keys: {allowed}."
            )
        if not value:
            raise SystemExit(
                f"Invalid --override value '{entry}'. Path cannot be empty."
            )
        overrides[key] = value
    return overrides


def _is_enabled_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "off", "no"}
    return bool(value)


def _module_is_enabled(module_config: dict[str, Any], variables: dict[str, Any]) -> bool:
    enabled_if = module_config.get("enabled_if")
    if enabled_if is None:
        return True
    if isinstance(enabled_if, bool):
        return enabled_if
    if isinstance(enabled_if, str):
        return _is_enabled_flag(variables.get(enabled_if))
    return _is_enabled_flag(enabled_if)


def _copy_repo_workspace(repo_root: Path, workspace_root: Path) -> None:
    shutil.copytree(
        repo_root,
        workspace_root,
        ignore=shutil.ignore_patterns(
            ".git",
            "build",
            "bin",
            "obj",
            "__pycache__",
            ".DS_Store",
            ".submit-output",
            "submit-output",
        ),
    )


def _replace_tree(target: Path, source: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def _stage_workspace_context(
    context: DefaultEvaluationContext,
) -> tuple[DefaultEvaluationContext, Path] | None:
    case_slug = context.case_root.name
    repo_case_root = context.repo_root / "cases" / case_slug
    repo_evaluator_root = context.repo_root / "evaluator" / case_slug
    needs_staging = context.case_root != repo_case_root or (
        context.evaluator_root is not None and context.evaluator_root != repo_evaluator_root
    )
    if not needs_staging:
        return None

    workspace_parent = Path(tempfile.mkdtemp(prefix="nitr_pipeline_workspace_"))
    workspace_root = workspace_parent / "repo"
    _copy_repo_workspace(context.repo_root, workspace_root)
    _replace_tree(workspace_root / "cases" / case_slug, context.case_root)
    if context.evaluator_root is not None:
        _replace_tree(workspace_root / "evaluator" / case_slug, context.evaluator_root)

    staged_context = DefaultEvaluationContext(
        repo_root=workspace_root.resolve(),
        case_root=(workspace_root / "cases" / case_slug).resolve(),
        baseline_case_root=(
            context.baseline_case_root.resolve()
            if context.baseline_case_root is not None
            else None
        ),
        evaluator_root=(workspace_root / "evaluator" / case_slug).resolve(),
        build_dir=(workspace_root / "build").resolve(),
        env=context.env,
        variables=context.variables,
    )
    return staged_context, workspace_parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path, help="Evaluation pipeline config file")
    parser.add_argument("--case_root", type=str, default=None)
    parser.add_argument("--baseline_case_root", type=str, default=None)
    parser.add_argument("--evaluator_root", type=str, default=None)
    parser.add_argument("--build_dir", type=str, default=None)
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=PATH",
        help=(
            "Override path fields from pipeline.json. "
            "Supported keys: case_root, baseline_case_root, build_dir"
        ),
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override pipeline variables, for example --set enable_hidden_evaluator=true",
    )
    args = parser.parse_args()

    config_path = args.config.resolve()
    config = _load_config(config_path)
    repo_root = Path(__file__).resolve().parents[1]
    config_base_dir = config_path.parent
    path_overrides = _parse_path_overrides(args.override)

    case_root = _resolve_override(
        args.case_root or path_overrides.get("case_root"),
        config,
        "case_root",
        default=repo_root,
        base_dir=config_base_dir,
    )
    baseline_case_root = _resolve_override(
        args.baseline_case_root or path_overrides.get("baseline_case_root"),
        config,
        "baseline_case_root",
        base_dir=config_base_dir,
    )
    evaluator_root = _resolve_override(
        args.evaluator_root,
        config,
        "evaluator_root",
        base_dir=config_base_dir,
    )
    build_dir = _resolve_override(
        args.build_dir or path_overrides.get("build_dir"),
        config,
        "build_dir",
        base_dir=config_base_dir,
    )

    variables = dict(config.get("variables", {}))
    variables.update(_parse_cli_variables(args.set))

    context = DefaultEvaluationContext(
        repo_root=repo_root,
        case_root=case_root.resolve(),
        baseline_case_root=baseline_case_root.resolve()
        if baseline_case_root is not None
        else None,
        evaluator_root=evaluator_root.resolve() if evaluator_root is not None else None,
        build_dir=build_dir.resolve() if build_dir is not None else None,
        env={
            key: str(value)
            for key, value in config.get("env", {}).items()
        },
        variables=variables,
    )
    staged = _stage_workspace_context(context)
    workspace_root: Path | None = None
    if staged is not None:
        context, workspace_root = staged

    modules = [
        module_from_config(module)
        for module in config.get("modules", [])
        if _module_is_enabled(module, variables)
    ]
    if not modules:
        raise SystemExit("Pipeline config requires a non-empty 'modules' list.")

    try:
        results = [module.run(context) for module in modules]
        failed = [result for result in results if not result.passed]
        payload = {
            "passed": not failed,
            "config": config_path.as_posix(),
            "case_root": context.case_root.as_posix(),
            "baseline_case_root": (
                context.baseline_case_root.as_posix()
                if context.baseline_case_root is not None
                else None
            ),
            "workspace_root": workspace_root.as_posix() if workspace_root else None,
            "summary": {
                "total_modules": len(results),
                "passed_modules": len(results) - len(failed),
                "failed_modules": len(failed),
            },
            "module_results": [result.to_payload() for result in results],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
        return CHECK_PASSED if payload["passed"] else CHECK_FAILED
    finally:
        if workspace_root is not None and workspace_root.exists():
            shutil.rmtree(workspace_root)


if __name__ == "__main__":
    sys.exit(main())
