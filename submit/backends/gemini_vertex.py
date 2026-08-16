"""Google Gemini on Vertex AI submission backend."""

from __future__ import annotations

import os
import time

from submit_common import require_config_value, run_case_submission, run_json_task


GEMINI_VERTEX_DEFAULTS = {
    "project_id": os.environ.get("NITR_GCP_PROJECT"),
    "region": os.environ.get("NITR_GCP_REGION", "global"),
    "model_name": "gemini-3.1-pro-preview",
    "response_delay_seconds": 60.0,
    "request_timeout_ms": 1800000,
    "request_retry_attempts": 3,
    "request_retry_delay_seconds": 300.0,
}


def call_gemini_vertex(client, genai, prompt: str, config: dict[str, object]):
    """Generate one Gemini response with the legacy retry behavior."""
    generate_config = genai.types.GenerateContentConfig(
        temperature=0.7,
        http_options={"timeout": config["request_timeout_ms"]},
    )
    response = None
    last_error = None
    attempts = int(config["request_retry_attempts"])
    for attempt in range(1, attempts + 1):
        try:
            response = client.models.generate_content(
                model=config["model_name"],
                contents=prompt,
                config=generate_config,
            )
            break
        except Exception as error:
            last_error = error
            print(f"[!] Request attempt {attempt}/{attempts} failed: {error}")
            if attempt == attempts:
                raise
            delay = float(config["request_retry_delay_seconds"])
            print(f"[*] Sleeping {delay:.1f}s before retry...")
            time.sleep(delay)
    if response is None:
        raise RuntimeError(f"Request failed without a response: {last_error}")
    return response.text


def run_gemini_vertex(args) -> None:
    """Run submissions through the Gemini Vertex SDK backend."""
    from google import genai

    config: dict[str, object] = GEMINI_VERTEX_DEFAULTS.copy()
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

    client = genai.Client(
        vertexai=True, project=config["project_id"], location=config["region"]
    )

    def run_single_task(
        input_project_dir, output_project_dir, task_file, response_output_path
    ):
        return run_json_task(
            input_project_dir,
            output_project_dir,
            task_file,
            response_output_path,
            fetch_response=lambda _project_dir, prompt, _response_output_path: (
                call_gemini_vertex(client, genai, prompt, config)
            ),
            request_label=config["model_name"],
            error_label="API Error",
            response_delay_seconds=config["response_delay_seconds"],
            payload_error_message="No valid JSON payload found in the AI response.",
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
