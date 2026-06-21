#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

from docker_runtime import (
    add_common_runtime_args,
    current_default_dockerfile,
    exit_after_docker_run,
)


def run_command(cmd, cwd, stream_output=False, timeout_seconds=None, env=None):
    """Run a subprocess and return a normalized result payload for reports."""
    print(f"[*] Running: {' '.join(cmd)}")
    if not stream_output:
        try:
            completed = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
                env=env,
            )
            return {
                "cmd": cmd,
                "cwd": str(cwd),
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "cmd": cmd,
                "cwd": str(cwd),
                "exit_code": 124,
                "stdout": exc.stdout or "",
                "stderr": (exc.stderr or "")
                + f"\nTimed out after {timeout_seconds} seconds.",
                "timed_out": True,
            }

    process = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    combined_output = []
    assert process.stdout is not None
    deadline = None if timeout_seconds is None else time.monotonic() + timeout_seconds
    timed_out = False
    try:
        while True:
            if deadline is not None and time.monotonic() > deadline:
                timed_out = True
                process.kill()
                break
            line = process.stdout.readline()
            if line:
                print(line, end="")
                combined_output.append(line)
                continue
            if process.poll() is not None:
                break
            time.sleep(0.1)
    finally:
        process.wait()

    return_code = 124 if timed_out else process.returncode
    stderr = "" if not timed_out else f"Timed out after {timeout_seconds} seconds."
    return {
        "cmd": cmd,
        "cwd": str(cwd),
        "exit_code": return_code,
        "stdout": "".join(combined_output),
        "stderr": stderr,
        "timed_out": timed_out,
    }


def resolve_cases_root(input_dir: Path) -> Path:
    """Accept either the repo root or a direct cases directory and normalize to cases/."""
    repo_cases_dir = input_dir / "cases"
    if repo_cases_dir.is_dir():
        return repo_cases_dir
    if input_dir.is_dir():
        return input_dir
    raise FileNotFoundError(f"Cases root not found under: {input_dir}")


def find_case_slug(cases_root: Path, case_id: str) -> str:
    """Resolve a zero-padded case id to its single matching directory name."""
    prefix = f"{case_id}."
    matches = sorted(
        entry.name
        for entry in cases_root.iterdir()
        if entry.is_dir() and entry.name.startswith(prefix)
    )
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected exactly one case for {case_id}, found: {matches}"
        )
    return matches[0]


def copy_repo_workspace(repo_root: Path, workspace_root: Path):
    """Create a clean temporary repo copy that can be mutated for one evaluation run."""
    if workspace_root.exists():
        shutil.rmtree(workspace_root)
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


def replace_case_dir(workspace_root: Path, case_slug: str, generated_case_dir: Path):
    """Swap the case under test into the temporary workspace copy."""
    target_case_dir = workspace_root / "cases" / case_slug
    if target_case_dir.exists():
        shutil.rmtree(target_case_dir)
    shutil.copytree(generated_case_dir, target_case_dir)


def replace_evaluator_dir(
    workspace_root: Path, case_slug: str, generated_evaluator_dir: Path
):
    """Swap in a generated evaluator when the submission produced one."""
    target_evaluator_dir = workspace_root / "evaluator" / case_slug
    if target_evaluator_dir.exists():
        shutil.rmtree(target_evaluator_dir)
    shutil.copytree(generated_evaluator_dir, target_evaluator_dir)


def ensure_generated_evaluator(
    repo_root: Path, generated_root: Path, case_slug: str
) -> Path:
    """Populate a missing generated evaluator from the repo baseline."""
    source_evaluator_dir = repo_root / "evaluator" / case_slug
    target_evaluator_dir = generated_root / "evaluator" / case_slug
    if target_evaluator_dir.is_dir():
        return target_evaluator_dir
    target_evaluator_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_evaluator_dir, target_evaluator_dir)
    return target_evaluator_dir


def refresh_generated_evaluator(
    repo_root: Path, generated_root: Path, case_slug: str
) -> Path:
    """Overwrite the generated evaluator with a fresh copy from the repo baseline."""
    source_evaluator_dir = repo_root / "evaluator" / case_slug
    target_evaluator_dir = generated_root / "evaluator" / case_slug
    if target_evaluator_dir.exists():
        shutil.rmtree(target_evaluator_dir)
    target_evaluator_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_evaluator_dir, target_evaluator_dir)
    return target_evaluator_dir


def discover_structural_checks(checks_dir: Path):
    """Find structural-check entrypoints, preferring a dedicated run_evaluator.py wrapper."""
    if not checks_dir.is_dir():
        return []

    python_scripts = sorted(
        path for path in checks_dir.iterdir() if path.is_file() and path.suffix == ".py"
    )

    if any(path.name == "run_evaluator.py" for path in python_scripts):
        python_scripts = [checks_dir / "run_evaluator.py"]

    return python_scripts


def structural_check_args(
    script_path: Path, case_root: Path, baseline_case_root: Path | None = None
):
    """Infer the argument shape expected by a structural-check script."""
    text = script_path.read_text(encoding="utf-8", errors="replace")
    args = []
    if "--case_root" in text:
        args.extend(["--case_root", str(case_root)])
    if "--baseline_case_root" in text and baseline_case_root is not None:
        args.extend(["--baseline_case_root", str(baseline_case_root)])
    if args:
        return args
    if "--case_dir" in text:
        return ["--case_dir", str(case_root)]
    if (
        "sys.argv[1]" in text
        or "Path(sys.argv[1])" in text
        or "pathlib.Path(sys.argv[1])" in text
    ):
        return [str(case_root)]
    return []


def run_structural_check(
    script_path: Path,
    workspace_root: Path,
    case_root: Path,
    timeout_seconds: int,
    baseline_case_root: Path | None = None,
):
    """Execute one structural-check script with the best-effort argument convention."""
    if script_path.suffix != ".py":
        raise ValueError(f"Unsupported check script: {script_path}")
    env = os.environ.copy()
    pythonpath_entries = [str(workspace_root)]
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_entries.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    cmd = [
        sys.executable,
        str(script_path),
        *structural_check_args(script_path, case_root, baseline_case_root),
    ]
    return run_command(
        cmd,
        workspace_root,
        timeout_seconds=timeout_seconds,
        env=env,
    )


def save_summary(summary: dict, generated_root: Path, case_slug: str):
    """Persist the evaluator summary next to the generated case outputs."""
    reports_dir = generated_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{case_slug}.json"
    report_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report_path


def discover_generated_roots(generated_root: Path) -> list[Path]:
    """Accept either one run root or a backend root containing runXX subdirectories."""
    direct_cases_dir = generated_root / "cases"
    if direct_cases_dir.is_dir():
        return [generated_root]

    run_roots = sorted(
        path
        for path in generated_root.iterdir()
        if path.is_dir() and path.name.startswith("run")
    )
    if run_roots:
        return run_roots

    raise FileNotFoundError(
        f"Generated cases directory not found under {generated_root}. "
        "Expected either cases/<case> or runXX/cases/<case>."
    )


def evaluate_generated_case(
    *,
    generated_root: Path,
    repo_root: Path,
    cases_root: Path,
    case_id: str,
    refresh_evaluator: bool,
    keep_workspace: bool,
    workspace_dir: Path | None,
    build_timeout: int,
    ctest_timeout: int,
    check_timeout: int,
) -> dict:
    """Evaluate one generated root for one case and return the summary payload."""
    case_slug = find_case_slug(cases_root, case_id)
    generated_case_dir = generated_root / "cases" / case_slug
    if not generated_case_dir.is_dir():
        raise FileNotFoundError(
            f"Generated case directory not found: {generated_case_dir}"
        )
    if refresh_evaluator:
        generated_evaluator_dir = refresh_generated_evaluator(
            repo_root, generated_root, case_slug
        )
    else:
        generated_evaluator_dir = ensure_generated_evaluator(
            repo_root, generated_root, case_slug
        )

    temp_dir = None
    local_workspace_dir = workspace_dir
    if local_workspace_dir is None:
        if keep_workspace:
            local_workspace_dir = Path(tempfile.mkdtemp(prefix=f"nitr_eval_{case_id}_"))
            print(f"[*] Keeping evaluator workspace at: {local_workspace_dir}")
        else:
            temp_dir = tempfile.TemporaryDirectory(prefix=f"nitr_eval_{case_id}_")
            local_workspace_dir = Path(temp_dir.name)

    summary = {
        "case_id": case_id,
        "case_slug": case_slug,
        "generated_root": str(generated_root),
        "generated_case_dir": str(generated_case_dir),
        "generated_evaluator_dir": str(generated_evaluator_dir),
        "workspace_dir": str(local_workspace_dir),
        "configure": None,
        "build": None,
        "ctest": None,
        "checks": [],
        "passed": False,
    }

    try:
        copy_repo_workspace(repo_root, local_workspace_dir)
        replace_case_dir(local_workspace_dir, case_slug, generated_case_dir)
        replace_evaluator_dir(local_workspace_dir, case_slug, generated_evaluator_dir)

        build_dir = local_workspace_dir / "build"
        case_root = local_workspace_dir / "cases" / case_slug
        baseline_case_root = repo_root / "cases" / case_slug
        evaluator_dir = local_workspace_dir / "evaluator" / case_slug

        configure_cmd = [
            "cmake",
            "-S",
            str(local_workspace_dir),
            "-B",
            str(build_dir),
            "-DNITR_BUILD_ALL_CASES=OFF",
            f"-DNITR_CASE={case_slug}",
            "-DNITR_BUILD_EVALUATOR=ON",
            f"-DNITR_BASELINE_CASES_ROOT={repo_root / 'cases'}",
        ]
        summary["configure"] = run_command(configure_cmd, local_workspace_dir)
        if summary["configure"]["exit_code"] == 0:
            build_cmd = ["cmake", "--build", str(build_dir)]
            summary["build"] = run_command(
                build_cmd,
                local_workspace_dir,
                stream_output=True,
                timeout_seconds=build_timeout,
            )
            if summary["build"]["exit_code"] == 0:
                summary["ctest"] = run_ctest_per_test(build_dir, ctest_timeout)

        for script_path in discover_structural_checks(evaluator_dir / "checks"):
            result = run_structural_check(
                script_path,
                local_workspace_dir,
                case_root,
                timeout_seconds=check_timeout,
                baseline_case_root=baseline_case_root,
            )
            result["script"] = str(script_path.relative_to(local_workspace_dir))
            summary["checks"].append(result)

        summary["passed"] = (
            summary["configure"]["exit_code"] == 0
            and summary["build"] is not None
            and summary["build"]["exit_code"] == 0
            and summary["ctest"] is not None
            and summary["ctest"]["exit_code"] == 0
            and all(result["exit_code"] == 0 for result in summary["checks"])
        )
        report_path = save_summary(summary, generated_root, case_slug)
        summary["report_path"] = str(report_path)
        print(f"[*] Saved report to: {report_path}")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return summary
    except Exception as exc:
        setattr(exc, "_nitr_workspace_dir", str(local_workspace_dir))
        raise
    finally:
        if temp_dir is not None and not keep_workspace:
            temp_dir.cleanup()


def aggregate_run_summaries(
    generated_root: Path, case_id: str, case_slug: str, run_summaries: list[dict]
) -> dict:
    """Aggregate multiple run-level summaries into Pass@N and Stability metrics."""
    submission_count = len(run_summaries)
    passed_values = [bool(summary["passed"]) for summary in run_summaries]
    pass_at_n = any(passed_values)
    stability = 1 if all(value == passed_values[0] for value in passed_values) else 0

    aggregate = {
        "case_id": case_id,
        "case_slug": case_slug,
        "generated_root": str(generated_root),
        "submission_count": submission_count,
        "pass_at": {
            "name": f"Pass@{submission_count}",
            "n": submission_count,
            "value": 1 if pass_at_n else 0,
        },
        "stability": {
            "name": "Stability",
            "n": submission_count,
            "value": stability,
        },
        "passed_runs": sum(1 for value in passed_values if value),
        "failed_runs": sum(1 for value in passed_values if not value),
        "evaluation_errors": sum(
            1 for summary in run_summaries if summary.get("evaluation_error")
        ),
        "passed": pass_at_n,
        "runs": [
            {
                "run_name": Path(summary["generated_root"]).name,
                "generated_root": summary["generated_root"],
                "passed": summary["passed"],
                "report_path": summary.get("report_path"),
                "evaluation_error": summary.get("evaluation_error"),
            }
            for summary in run_summaries
        ],
    }
    report_path = save_summary(aggregate, generated_root, case_slug)
    aggregate["report_path"] = str(report_path)
    return aggregate


def build_error_summary(
    *, generated_root: Path, case_id: str, case_slug: str, error: Exception
) -> dict:
    """Build a minimal per-run summary for evaluator crashes."""
    return {
        "case_id": case_id,
        "case_slug": case_slug,
        "generated_root": str(generated_root),
        "passed": False,
        "evaluation_error": {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        },
        "workspace_dir": getattr(error, "_nitr_workspace_dir", None),
    }


def discover_ctest_names(build_dir: Path):
    """Ask CTest for the concrete test names so failures can be reported per test."""
    result = run_command(
        ["ctest", "--test-dir", str(build_dir), "-N", "--show-only=json-v1"],
        build_dir,
    )
    if result["exit_code"] != 0:
        return result, []

    payload = json.loads(result["stdout"])
    tests = payload.get("tests", [])
    names = [test["name"] for test in tests if "name" in test]
    return result, names


def is_case_relevant_ctest(test_name: str) -> bool:
    """Filter out repo-level tests that should not affect one-case evaluation."""
    return test_name not in {"nitr_format_check", "nitr_python_format_check"}


def run_ctest_per_test(build_dir: Path, timeout_seconds: int):
    """Run each discovered CTest test separately to keep logs and timeouts isolated."""
    discover_result, test_names = discover_ctest_names(build_dir)
    relevant_test_names = [name for name in test_names if is_case_relevant_ctest(name)]
    summary = {
        "discover": discover_result,
        "tests": [],
        "skipped_tests": [
            name for name in test_names if not is_case_relevant_ctest(name)
        ],
        "exit_code": 0,
        "timed_out": False,
    }
    if discover_result["exit_code"] != 0:
        summary["exit_code"] = discover_result["exit_code"]
        return summary

    for test_name in relevant_test_names:
        cmd = [
            "ctest",
            "--test-dir",
            str(build_dir),
            "--output-on-failure",
            "--timeout",
            str(timeout_seconds),
            "-R",
            f"^{test_name}$",
        ]
        result = run_command(
            cmd, build_dir, stream_output=True, timeout_seconds=timeout_seconds + 5
        )
        result["test_name"] = test_name
        summary["tests"].append(result)
        if result["exit_code"] != 0:
            summary["exit_code"] = result["exit_code"]
            summary["timed_out"] = summary["timed_out"] or result.get(
                "timed_out", False
            )

    return summary


def main():
    """Build a temporary workspace, run tests, then emit a machine-readable report."""
    parser = argparse.ArgumentParser(
        description="Build one generated case, run functional tests via CTest, and then run structural checks."
    )
    parser.add_argument(
        "--generated-root",
        "--generated_root",
        "-g",
        dest="generated_root",
        required=True,
        help="Generated root containing cases/<case> and optional evaluator/<case>",
    )
    parser.add_argument(
        "--case-id",
        "--case_id",
        "-c",
        dest="case_id",
        required=True,
        help="Three-digit case id, e.g. 018",
    )
    parser.add_argument(
        "--repo-root",
        "--repo_root",
        "-r",
        dest="repo_root",
        default=".",
        help="Repo root or cases root",
    )
    parser.add_argument(
        "--keep-workspace",
        "--keep_workspace",
        dest="keep_workspace",
        action="store_true",
        help="Keep the temporary workspace directory",
    )
    parser.add_argument(
        "--workspace-dir",
        "--workspace_dir",
        dest="workspace_dir",
        help="Optional workspace directory to use instead of a temp dir",
    )
    parser.add_argument(
        "--refresh-evaluator",
        "--refresh_evaluator",
        dest="refresh_evaluator",
        action="store_true",
        help="Overwrite generated_root/evaluator/<case> with the current repo evaluator before running",
    )
    parser.add_argument(
        "--build-timeout",
        "--build_timeout",
        dest="build_timeout",
        type=int,
        default=300,
        help="Timeout in seconds for the build step",
    )
    parser.add_argument(
        "--ctest-timeout",
        "--ctest_timeout",
        dest="ctest_timeout",
        type=int,
        default=120,
        help="Timeout in seconds for the functional test step",
    )
    parser.add_argument(
        "--check-timeout",
        "--check_timeout",
        dest="check_timeout",
        type=int,
        default=60,
        help="Timeout in seconds for each Python structural check",
    )
    add_common_runtime_args(parser, default_dockerfile=current_default_dockerfile())
    args = parser.parse_args()

    case_id = args.case_id.zfill(3)
    generated_root = Path(args.generated_root).resolve()
    input_root = Path(args.repo_root).resolve()
    cases_root = resolve_cases_root(input_root)
    repo_root = cases_root.parent

    if args.runtime == "docker":
        if args.keep_workspace and not args.workspace_dir:
            raise ValueError(
                "--keep_workspace with --runtime docker requires --workspace_dir so the workspace persists on the host."
            )

        forwarded_args = [
            "--generated-root",
            str(generated_root),
            "--case-id",
            args.case_id,
            "--repo-root",
            str(repo_root),
            "--build-timeout",
            str(args.build_timeout),
            "--ctest-timeout",
            str(args.ctest_timeout),
            "--check-timeout",
            str(args.check_timeout),
        ]
        if args.refresh_evaluator:
            forwarded_args.append("--refresh-evaluator")
        if args.keep_workspace:
            forwarded_args.append("--keep-workspace")
        if args.workspace_dir:
            workspace_mount_root = Path(args.workspace_dir).resolve()
            if not workspace_mount_root.exists():
                workspace_mount_root = workspace_mount_root.parent
            forwarded_args.extend(
                ["--workspace-dir", str(Path(args.workspace_dir).resolve())]
            )
        extra_mount_roots = [generated_root]
        if args.workspace_dir:
            extra_mount_roots.append(workspace_mount_root)
        exit_after_docker_run(
            args=args,
            repo_root=repo_root,
            script_path="submit/run_case_evaluator.py",
            forwarded_args=forwarded_args,
            path_arg_names={"--generated-root", "--repo-root", "--workspace-dir"},
            extra_mount_roots=extra_mount_roots,
        )

    run_roots = discover_generated_roots(generated_root)
    evaluating_backend_root = generated_root != run_roots[0]
    if len(run_roots) == 1 and not evaluating_backend_root:
        summary = evaluate_generated_case(
            generated_root=run_roots[0],
            repo_root=repo_root,
            cases_root=cases_root,
            case_id=case_id,
            refresh_evaluator=args.refresh_evaluator,
            keep_workspace=args.keep_workspace,
            workspace_dir=Path(args.workspace_dir).resolve()
            if args.workspace_dir
            else None,
            build_timeout=args.build_timeout,
            ctest_timeout=args.ctest_timeout,
            check_timeout=args.check_timeout,
        )
        raise SystemExit(0 if summary["passed"] else 1)

    case_slug = find_case_slug(cases_root, case_id)
    print(
        f"[*] Evaluating {case_slug} across {len(run_roots)} submission runs under "
        f"{generated_root}"
    )
    run_summaries = []
    for run_root in run_roots:
        print(f"===== RUN {run_root.name} =====")
        run_workspace_dir = None
        if args.workspace_dir:
            run_workspace_dir = Path(args.workspace_dir).resolve() / run_root.name
        try:
            run_summaries.append(
                evaluate_generated_case(
                    generated_root=run_root,
                    repo_root=repo_root,
                    cases_root=cases_root,
                    case_id=case_id,
                    refresh_evaluator=args.refresh_evaluator,
                    keep_workspace=args.keep_workspace,
                    workspace_dir=run_workspace_dir,
                    build_timeout=args.build_timeout,
                    ctest_timeout=args.ctest_timeout,
                    check_timeout=args.check_timeout,
                )
            )
        except Exception as exc:
            error_summary = build_error_summary(
                generated_root=run_root,
                case_id=case_id,
                case_slug=case_slug,
                error=exc,
            )
            print(f"[!] RUN {run_root.name} evaluation error: {exc}")
            try:
                report_path = save_summary(error_summary, run_root, case_slug)
                error_summary["report_path"] = str(report_path)
                print(f"[*] Saved error report to: {report_path}")
            except Exception as save_exc:
                error_summary["report_save_error"] = {
                    "type": type(save_exc).__name__,
                    "message": str(save_exc),
                }
                print(
                    f"[!] Failed to save error report for {run_root.name}: {save_exc}"
                )
            run_summaries.append(error_summary)

    aggregate = aggregate_run_summaries(
        generated_root, case_id, case_slug, run_summaries
    )
    print(f"[*] Saved aggregate report to: {aggregate['report_path']}")
    print(json.dumps(aggregate, indent=2, ensure_ascii=False))
    raise SystemExit(
        0 if aggregate["passed"] and aggregate["evaluation_errors"] == 0 else 1
    )


if __name__ == "__main__":
    main()
