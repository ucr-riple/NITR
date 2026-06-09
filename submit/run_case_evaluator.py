#!/usr/bin/env python3

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def run_command(cmd, cwd, stream_output=False, timeout_seconds=None):
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


def structural_check_args(script_path: Path, case_root: Path):
    """Infer the argument shape expected by a structural-check script."""
    text = script_path.read_text(encoding="utf-8", errors="replace")
    if "--case_root" in text:
        return ["--case_root", str(case_root)]
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
    script_path: Path, workspace_root: Path, case_root: Path, timeout_seconds: int
):
    """Execute one structural-check script with the best-effort argument convention."""
    if script_path.suffix != ".py":
        raise ValueError(f"Unsupported check script: {script_path}")
    cmd = [
        sys.executable,
        str(script_path),
        *structural_check_args(script_path, case_root),
    ]
    return run_command(cmd, workspace_root, timeout_seconds=timeout_seconds)


def save_summary(summary: dict, generated_root: Path, case_slug: str):
    """Persist the evaluator summary next to the generated case outputs."""
    reports_dir = generated_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{case_slug}.json"
    report_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    summary["report_path"] = str(report_path)
    return report_path


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
    return test_name != "nitr_format_check"


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
        "--generated_root",
        "-g",
        required=True,
        help="Generated root containing cases/<case> and optional evaluator/<case>",
    )
    parser.add_argument(
        "--case_id", "-c", required=True, help="Three-digit case id, e.g. 018"
    )
    parser.add_argument(
        "--repo_root", "-r", default=".", help="Repo root or cases root"
    )
    parser.add_argument(
        "--keep_workspace",
        action="store_true",
        help="Keep the temporary workspace directory",
    )
    parser.add_argument(
        "--workspace_dir",
        help="Optional workspace directory to use instead of a temp dir",
    )
    parser.add_argument(
        "--refresh_evaluator",
        action="store_true",
        help="Overwrite generated_root/evaluator/<case> with the current repo evaluator before running",
    )
    parser.add_argument(
        "--build_timeout",
        type=int,
        default=300,
        help="Timeout in seconds for the build step",
    )
    parser.add_argument(
        "--ctest_timeout",
        type=int,
        default=120,
        help="Timeout in seconds for the functional test step",
    )
    parser.add_argument(
        "--check_timeout",
        type=int,
        default=60,
        help="Timeout in seconds for each Python structural check",
    )
    args = parser.parse_args()

    case_id = args.case_id.zfill(3)
    generated_root = Path(args.generated_root).resolve()
    input_root = Path(args.repo_root).resolve()
    cases_root = resolve_cases_root(input_root)
    repo_root = cases_root.parent
    case_slug = find_case_slug(cases_root, case_id)
    generated_case_dir = generated_root / "cases" / case_slug
    if not generated_case_dir.is_dir():
        raise FileNotFoundError(
            f"Generated case directory not found: {generated_case_dir}"
        )
    if args.refresh_evaluator:
        generated_evaluator_dir = refresh_generated_evaluator(
            repo_root, generated_root, case_slug
        )
    else:
        generated_evaluator_dir = ensure_generated_evaluator(
            repo_root, generated_root, case_slug
        )

    workspace_dir = Path(args.workspace_dir).resolve() if args.workspace_dir else None
    temp_dir = None
    if workspace_dir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix=f"nitr_eval_{case_id}_")
        workspace_dir = Path(temp_dir.name)

    summary = {
        "case_id": case_id,
        "case_slug": case_slug,
        "generated_root": str(generated_root),
        "generated_case_dir": str(generated_case_dir),
        "generated_evaluator_dir": str(generated_evaluator_dir),
        "workspace_dir": str(workspace_dir),
        "configure": None,
        "build": None,
        "ctest": None,
        "checks": [],
        "passed": False,
    }

    try:
        copy_repo_workspace(repo_root, workspace_dir)
        replace_case_dir(workspace_dir, case_slug, generated_case_dir)
        replace_evaluator_dir(workspace_dir, case_slug, generated_evaluator_dir)

        build_dir = workspace_dir / "build"
        case_root = workspace_dir / "cases" / case_slug
        evaluator_dir = workspace_dir / "evaluator" / case_slug

        configure_cmd = [
            "cmake",
            "-S",
            str(workspace_dir),
            "-B",
            str(build_dir),
            "-DNITR_BUILD_ALL_CASES=OFF",
            f"-DNITR_CASE={case_slug}",
            "-DNITR_BUILD_EVALUATOR=ON",
        ]
        summary["configure"] = run_command(configure_cmd, workspace_dir)
        if summary["configure"]["exit_code"] == 0:
            build_cmd = ["cmake", "--build", str(build_dir)]
            summary["build"] = run_command(
                build_cmd,
                workspace_dir,
                stream_output=True,
                timeout_seconds=args.build_timeout,
            )
            if summary["build"]["exit_code"] == 0:
                summary["ctest"] = run_ctest_per_test(build_dir, args.ctest_timeout)

        for script_path in discover_structural_checks(evaluator_dir / "checks"):
            result = run_structural_check(
                script_path,
                workspace_dir,
                case_root,
                timeout_seconds=args.check_timeout,
            )
            result["script"] = str(script_path.relative_to(workspace_dir))
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
        print(f"[*] Saved report to: {report_path}")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        raise SystemExit(0 if summary["passed"] else 1)
    finally:
        if temp_dir is not None and not args.keep_workspace:
            temp_dir.cleanup()


if __name__ == "__main__":
    main()
