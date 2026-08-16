"""Anthropic Claude on Vertex AI submission backend."""

from __future__ import annotations

import os
import time

from submit_common import require_config_value, run_case_submission, run_json_task


CLAUDE_VERTEX_DEFAULTS = {
    "project_id": os.environ.get("NITR_GCP_PROJECT"),
    "region": os.environ.get("NITR_GCP_REGION", "global"),
    "model_name": "claude-opus-4-5@20251101",
    "response_delay_seconds": 60.0,
    "request_timeout_seconds": 1800.0,
    "request_retry_attempts": 3,
    "request_retry_delay_seconds": 300.0,
    "max_tokens": 32768,
}


def extract_claude_message_text(message) -> str:
    """Flatten Claude content blocks into one plain-text response string."""
    parts = []
    for block in getattr(message, "content", []):
        text = getattr(block, "text", None)
        if isinstance(text, str) and text:
            parts.append(text)
    if not parts:
        raise ValueError("Claude response did not contain any text blocks")
    return "".join(parts)


def call_claude_vertex(client, prompt: str, config: dict[str, object]) -> str:
    """Issue one Claude request with the legacy retry policy."""
    attempts = int(config["request_retry_attempts"])
    last_error = None
    for attempt in range(1, attempts + 1):
        started = time.time()
        print(
            f"[*] Request attempt {attempt}/{attempts} started at "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(started))}"
        )
        try:
            message = client.messages.create(
                model=config["model_name"],
                max_tokens=config["max_tokens"],
                messages=[{"role": "user", "content": prompt}],
                timeout=config["request_timeout_seconds"],
            )
            print(
                f"[*] Request attempt {attempt}/{attempts} succeeded in "
                f"{time.time() - started:.1f}s"
            )
            return extract_claude_message_text(message)
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


def run_claude_vertex(args) -> None:
    """Run submissions through Anthropic's Vertex-hosted Claude API."""
    from anthropic import AnthropicVertex

    config: dict[str, object] = CLAUDE_VERTEX_DEFAULTS.copy()
    if args.project_id:
        config["project_id"] = args.project_id
    if args.region:
        config["region"] = args.region
    if args.model_name:
        config["model_name"] = args.model_name
    require_config_value(
        config,
        "project_id",
        cli_flag="--project_id",
        env_var="NITR_GCP_PROJECT",
    )

    client = AnthropicVertex(region=config["region"], project_id=config["project_id"])

    def run_single_task(
        input_project_dir, output_project_dir, task_file, response_output_path
    ):
        return run_json_task(
            input_project_dir,
            output_project_dir,
            task_file,
            response_output_path,
            fetch_response=lambda _project_dir, prompt, _response_output_path: (
                call_claude_vertex(client, prompt, config)
            ),
            request_label="Claude",
            error_label="Claude Error",
            response_delay_seconds=config["response_delay_seconds"],
            payload_error_message="No valid JSON payload found in the Claude response.",
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
