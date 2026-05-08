#!/usr/bin/env python3
import subprocess
import sys
import os

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: test_functional.py <path_to_app_executable>")
        return 1

    app_exec = sys.argv[1]

    def run_test(target_temp: float, sim_temp: float, expected_output: str) -> bool:
        env = os.environ.copy()
        env["TMP26_SIMULATOR_TEMP"] = str(sim_temp)
        
        try:
            result = subprocess.run(
                [app_exec, str(target_temp)], 
                env=env, capture_output=True, text=True, check=True
            )
            output = result.stdout.strip()
            if output == expected_output:
                return True
            else:
                print(f"FAIL: Target {target_temp}, Sensor {sim_temp}. Expected '{expected_output}', got '{output}'")
                return False
        except subprocess.CalledProcessError as e:
            print(f"FAIL: Command failed with exit code {e.returncode}. Output: {e.stdout.strip()} {e.stderr.strip()}")
            return False

    cases = [
        (22.0, 18.5, "Heating"),
        (22.0, 19.0, "Heating"),
        (22.0, 20.0, "Heating"),
        (22.0, 20.01, "Idle"),
        (22.0, 22.0, "Idle"),
        (22.0, 23.99, "Idle"),
        (22.0, 24.0, "Cooling"),
        (22.0, 24.5, "Cooling"),
        (22.0, 30.0, "Cooling"),
    ]

    all_passed = True
    for target, sim, expected in cases:
        if not run_test(target, sim, expected):
            all_passed = False

    if all_passed:
        print("PASS: Functional test passed.")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
