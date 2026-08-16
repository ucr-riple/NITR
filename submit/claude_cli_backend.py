"""Claude Code CLI submission backend."""

from __future__ import annotations

import subprocess
import time

from submit_common import (
    apply_file_replacements,
    extract_json_payload,
    prepare_output_dir,
    run_case_submission,
    save_response_text,
)


CLAUDE_CLI_DEFAULTS = {
    "model_name": "claude-opus-4-6",
    "cli_timeout_seconds": 1800,
    "request_retry_attempts": 3,
    "request_retry_delay_seconds": 300.0,
    "response_delay_seconds": 10.0,
    "allowed_tools": "Read",
}


def combine_run_labels(*parts: str | None) -> str | None:
    """Join optional run-label fragments into one log label string."""
    filtered = [part for part in parts if part]
    if not filtered:
        return None
    return " ".join(filtered)


def transcript_output_path(response_output_path: str) -> str:
    """Derive the sidecar transcript filename for a saved backend response."""
    if response_output_path.endswith(".txt"):
        return response_output_path[:-4] + ".transcript.txt"
    return response_output_path + ".transcript.txt"


def build_claude_cli_prompt(task_file: str) -> str:
    """Build the stricter JSON-only prompt used for the Claude CLI agent."""
    return f"""Please complete the task described in {task_file}.
Read whatever files you need to understand the codebase first.
Then return only one JSON object with this exact shape:
{{
  "files": [
    {{
      "filename": "relative/path/to/file",
      "content": "full replacement file content"
    }}
  ]
}}
Include both modified AND newly created files.
Use project-relative file paths.
Do not include explanations, markdown fences, or any text outside the JSON object.
Do not return partial patches or diffs.
Focus only on the implementation requested in {task_file}."""


def build_claude_cli_command(
    prompt: str, model_name: str, allowed_tools: str
) -> list[str]:
    """Build the Claude CLI command without invoking it."""
    return [
        "claude",
        "-p",
        prompt,
        "--model",
        model_name,
        "--allowedTools",
        allowed_tools,
        "--output-format",
        "text",
    ]


def call_claude_cli(
    prompt: str,
    working_dir: str,
    response_output_path: str,
    config: dict[str, object],
) -> str:
    """Invoke Claude CLI with the legacy retry and transcript behavior."""
    command = build_claude_cli_command(
        prompt, str(config["model_name"]), str(config["allowed_tools"])
    )
    attempts = int(config["request_retry_attempts"])
    last_error = None
    for attempt in range(1, attempts + 1):
        started = time.time()
        print(
            f"[*] CLI attempt {attempt}/{attempts} started at "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(started))}"
        )
        try:
            result = subprocess.run(
                command,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=float(config["cli_timeout_seconds"]),
            )
            elapsed = time.time() - started
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            save_response_text(stdout, response_output_path)
            save_response_text(
                f"=== STDOUT ===\n{stdout}\n\n=== STDERR ===\n{stderr}",
                transcript_output_path(response_output_path),
            )
            if result.returncode != 0:
                print(
                    f"[!] CLI attempt {attempt} exited with code "
                    f"{result.returncode} after {elapsed:.1f}s"
                )
                print(f"    stderr: {stderr[:500]}")
                last_error = RuntimeError(
                    f"claude exited {result.returncode}: {stderr[:200]}"
                )
                if attempt < attempts:
                    delay = float(config["request_retry_delay_seconds"])
                    print(f"[*] Sleeping {delay:.1f}s before retry...")
                    time.sleep(delay)
                continue
            print(f"[*] CLI attempt {attempt}/{attempts} succeeded in {elapsed:.1f}s")
            return stdout
        except subprocess.TimeoutExpired:
            elapsed = time.time() - started
            last_error = TimeoutError(f"claude CLI timed out after {elapsed:.1f}s")
            print(f"[!] CLI attempt {attempt} timed out after {elapsed:.1f}s")
            if attempt < attempts:
                delay = float(config["request_retry_delay_seconds"])
                print(f"[*] Sleeping {delay:.1f}s before retry...")
                time.sleep(delay)
        except FileNotFoundError as error:
            raise RuntimeError(
                "claude CLI not found. Install with: "
                "npm install -g @anthropic-ai/claude-code"
            ) from error
    raise RuntimeError(f"All CLI attempts failed. Last error: {last_error}")


def run_claude_cli(args) -> None:
    """Run submissions through the local Claude Code CLI."""
    config: dict[str, object] = CLAUDE_CLI_DEFAULTS.copy()
    if args.model_name:
        config["model_name"] = args.model_name

    def run_single_task(
        input_project_dir, output_project_dir, task_file, response_output_path
    ):
        """Execute one task via Claude CLI and materialize the returned file set."""
        prepare_output_dir(input_project_dir, output_project_dir)
        prompt = build_claude_cli_prompt(task_file)
        print(
            "[*] Invoking Claude CLI at "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}..."
        )
        try:
            stdout = call_claude_cli(
                prompt, output_project_dir, response_output_path, config
            )
            payload = extract_json_payload(stdout)
            if not payload:
                print("[-] No valid JSON payload found in the Claude CLI response.")
                return False
            apply_file_replacements(payload, output_project_dir)
            delay = float(config["response_delay_seconds"])
            if delay > 0:
                print(f"[*] Sleeping {delay:.1f}s after successful patch...")
                time.sleep(delay)
            print("[*] Patched project copy created successfully.")
            return True
        except Exception as error:
            print(f"[!] CLI Error: {error}")
            return False

    run_case_submission(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        case_id=args.case_id,
        run_single_task=run_single_task,
        start_step=args.start_step or 1,
        end_step=args.end_step,
        run_label=combine_run_labels(getattr(args, "run_label", None), "(CLI agent)"),
    )
