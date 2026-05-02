#!/usr/bin/env python3
import subprocess
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: test_functional.py <path_to_app_executable>")
        return 1

    app_exec = sys.argv[1]

    try:
        result = subprocess.run(
            [app_exec],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(
            f"FAIL: app exited with {e.returncode}. "
            f"stdout={e.stdout.strip()} stderr={e.stderr.strip()}"
        )
        return 1

    output = result.stdout.strip()
    lines = [line.strip() for line in output.splitlines() if line.strip()]

    failures = []

    if not any(line.startswith("alice:") for line in lines):
        failures.append("expected valid submission for alice to be graded")

    if not any(line.startswith("dana:") for line in lines):
        failures.append("expected valid submission for dana to be graded")

    if any(line.startswith("bob:") for line in lines):
        failures.append("empty submission for bob should not be graded")

    if any(line.startswith("carol:") for line in lines):
        failures.append("late submission for carol should not be graded")

    if "Processed 2 submissions" not in lines:
        failures.append(
            "expected reporter summary to say: Processed 2 submissions"
        )

    if failures:
        print("FAIL: Functional app test failed:")
        for failure in failures:
            print(f"- {failure}")
        print("App output:")
        print(output)
        return 1

    print("PASS: Functional tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
