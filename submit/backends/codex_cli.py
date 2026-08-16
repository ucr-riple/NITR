"""Codex CLI submission backend."""

from __future__ import annotations

import json
import os
import subprocess
import time

from submit_common import (
    run_case_submission,
    run_json_task,
    save_json_payload,
    usage_output_path,
)


CODEX_CLI_DEFAULTS = {
    "model_name": "gpt-5.4",
    "response_delay_seconds": 60.0,
    "request_timeout_seconds": 1800.0,
    "request_retry_attempts": 3,
    "request_retry_delay_seconds": 300.0,
}


def build_codex_cli_command(
    project_dir: str, model_name: str, temp_output_path: str
) -> list[str]:
    """Build the read-only Codex CLI command without invoking it."""
    return [
        "codex",
        "exec",
        "--model",
        model_name,
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "-C",
        project_dir,
        "--json",
        "--output-last-message",
        temp_output_path,
        "-",
    ]


def extract_codex_usage_from_events(stdout_text: str) -> dict[str, object]:
    """Best-effort extraction of usage details from Codex JSONL event output."""
    usage = None
    usage_event_type = None

    for raw_line in stdout_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue

        candidate = None
        if isinstance(event.get("usage"), dict):
            candidate = event.get("usage")
        elif isinstance(event.get("token_usage"), dict):
            candidate = event.get("token_usage")
        elif isinstance(event.get("result"), dict):
            result = event["result"]
            if isinstance(result.get("usage"), dict):
                candidate = result.get("usage")
            elif isinstance(result.get("token_usage"), dict):
                candidate = result.get("token_usage")

        if isinstance(candidate, dict):
            usage = candidate
            usage_event_type = event.get("type")

    if usage is None:
        return {
            "available": False,
            "backend": "chatgpt-codex",
            "reason": "codex exec JSON event stream did not include a usage payload",
        }
    return {
        "available": True,
        "backend": "chatgpt-codex",
        "event_type": usage_event_type,
        "usage": usage,
    }


def call_codex_cli(
    project_dir: str,
    prompt: str,
    temp_output_path: str,
    config: dict[str, object],
) -> tuple[str, dict[str, object]]:
    """Invoke Codex CLI and return its last message and usage metadata."""
    attempts = int(config["request_retry_attempts"])
    last_error = None
    for attempt in range(1, attempts + 1):
        started = time.time()
        print(
            f"[*] Request attempt {attempt}/{attempts} started at "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(started))}"
        )
        try:
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)
            completed = subprocess.run(
                build_codex_cli_command(
                    project_dir, str(config["model_name"]), temp_output_path
                ),
                input=prompt,
                text=True,
                capture_output=True,
                timeout=float(config["request_timeout_seconds"]),
                check=False,
            )
            if completed.returncode != 0:
                stderr = completed.stderr.strip()
                stdout = completed.stdout.strip()
                details = (
                    stderr or stdout or f"codex exec exited with {completed.returncode}"
                )
                raise RuntimeError(details)
            if not os.path.isfile(temp_output_path):
                raise ValueError(
                    "codex exec did not produce an output-last-message file"
                )
            with open(temp_output_path, "r", encoding="utf-8") as output_file:
                response_text = output_file.read()
            os.remove(temp_output_path)
            if not response_text.strip():
                raise ValueError("codex exec produced an empty last message")
            print(
                f"[*] Request attempt {attempt}/{attempts} succeeded in "
                f"{time.time() - started:.1f}s"
            )
            return response_text, extract_codex_usage_from_events(completed.stdout)
        except Exception as error:
            last_error = error
            print(
                f"[!] Request attempt {attempt}/{attempts} failed after "
                f"{time.time() - started:.1f}s: {error}"
            )
            if attempt == attempts:
                raise
            delay = float(config["request_retry_delay_seconds"])
            print(f"[*] Sleeping {delay:.1f}s before retry...")
            time.sleep(delay)
    raise RuntimeError(f"Request failed without a response: {last_error}")


def run_chatgpt_codex(args) -> None:
    """Run submissions through the local Codex CLI in read-only mode."""
    config: dict[str, object] = CODEX_CLI_DEFAULTS.copy()
    if args.model_name:
        config["model_name"] = args.model_name

    def run_single_task(
        input_project_dir, output_project_dir, task_file, response_output_path
    ):
        """Execute one task through Codex and apply the returned JSON patch."""

        def fetch_response(project_dir, prompt, _response_output_path):
            response_text, usage_payload = call_codex_cli(
                project_dir,
                prompt,
                os.path.join(project_dir, ".codex_last_message.txt"),
                config,
            )
            save_json_payload(usage_payload, usage_output_path(response_output_path))
            return response_text

        return run_json_task(
            input_project_dir,
            output_project_dir,
            task_file,
            response_output_path,
            fetch_response=fetch_response,
            request_label="ChatGPT",
            error_label="ChatGPT Error",
            response_delay_seconds=config["response_delay_seconds"],
            allow_empty_files=True,
            payload_error_message="No valid JSON payload found in the ChatGPT response.",
        )

    run_case_submission(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        case_id=args.case_id,
        run_single_task=run_single_task,
        start_step=args.start_step or 1,
        end_step=args.end_step,
        run_label=getattr(args, "run_label", None),
    )
