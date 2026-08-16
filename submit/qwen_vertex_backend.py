"""Qwen on a user-managed Vertex endpoint submission backend."""

from __future__ import annotations

import os
import time

from submit_common import require_config_value, run_case_submission, run_json_task


QWEN_VERTEX_DEFAULTS = {
    "project_id": os.environ.get("NITR_GCP_PROJECT"),
    "endpoint_location": os.environ.get("NITR_VERTEX_ENDPOINT_LOCATION"),
    "endpoint_id": os.environ.get("NITR_VERTEX_ENDPOINT_ID"),
    "request_format": "prompt",
    "response_delay_seconds": 60.0,
    "request_timeout_seconds": 1800.0,
    "request_retry_attempts": 3,
    "request_retry_delay_seconds": 300.0,
    "max_tokens": 16384,
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 40,
}


def build_qwen_vertex_payload(
    prompt: str, config: dict[str, object]
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    """Translate a prompt into the endpoint's configured request format."""
    if config["request_format"] == "chat":
        return [
            {
                "@requestFormat": "chatCompletions",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": config["max_tokens"],
                "temperature": config["temperature"],
                "top_p": config["top_p"],
                "top_k": config["top_k"],
            }
        ], None
    return [{"prompt": prompt}], {
        "max_tokens": config["max_tokens"],
        "temperature": config["temperature"],
        "top_p": config["top_p"],
        "top_k": config["top_k"],
    }


def extract_qwen_vertex_text(prediction) -> str:
    """Normalize supported Vertex prediction payload shapes into text."""
    if isinstance(prediction, str):
        return prediction
    if isinstance(prediction, dict):
        for key in ("text", "generated_text", "output_text", "response", "content"):
            value = prediction.get(key)
            if isinstance(value, str):
                return value
        choices = prediction.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
        candidates = prediction.get("candidates")
        if isinstance(candidates, list) and candidates:
            first = candidates[0]
            if isinstance(first, dict):
                content = first.get("content")
                if isinstance(content, str):
                    return content
                parts = first.get("parts")
                if isinstance(parts, list):
                    texts = [
                        part.get("text")
                        for part in parts
                        if isinstance(part, dict) and isinstance(part.get("text"), str)
                    ]
                    if texts:
                        return "".join(texts)
        predictions = prediction.get("predictions")
        if isinstance(predictions, list) and predictions:
            return extract_qwen_vertex_text(predictions[0])
    if isinstance(prediction, list) and prediction:
        return extract_qwen_vertex_text(prediction[0])
    raise ValueError(
        f"Unsupported endpoint prediction payload shape: {type(prediction).__name__}"
    )


def call_qwen_vertex(endpoint, prompt: str, config: dict[str, object]) -> str:
    """Call the configured endpoint with the legacy retry policy."""
    instances, parameters = build_qwen_vertex_payload(prompt, config)
    attempts = int(config["request_retry_attempts"])
    last_error = None
    for attempt in range(1, attempts + 1):
        started = time.time()
        print(
            f"[*] Request attempt {attempt}/{attempts} started at "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(started))}"
        )
        try:
            prediction = endpoint.predict(
                instances=instances,
                parameters=parameters,
                timeout=config["request_timeout_seconds"],
            )
            if not prediction.predictions:
                raise ValueError("Endpoint returned no predictions")
            first_prediction = prediction.predictions
            if isinstance(first_prediction, list):
                if not first_prediction:
                    raise ValueError("Endpoint returned empty predictions list")
                first_prediction = first_prediction[0]
            print(
                f"[*] Request attempt {attempt}/{attempts} succeeded in "
                f"{time.time() - started:.1f}s"
            )
            return extract_qwen_vertex_text(first_prediction)
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


def run_qwen_vertex(args) -> None:
    """Run submissions against a user-managed Vertex endpoint serving Qwen."""
    from google.cloud import aiplatform

    config: dict[str, object] = QWEN_VERTEX_DEFAULTS.copy()
    if args.project_id:
        config["project_id"] = args.project_id
    if args.endpoint_id:
        config["endpoint_id"] = args.endpoint_id
    if args.endpoint_location:
        config["endpoint_location"] = args.endpoint_location
    require_config_value(
        config, "project_id", cli_flag="--project_id", env_var="NITR_GCP_PROJECT"
    )
    require_config_value(
        config,
        "endpoint_id",
        cli_flag="--endpoint_id",
        env_var="NITR_VERTEX_ENDPOINT_ID",
    )
    require_config_value(
        config,
        "endpoint_location",
        cli_flag="--endpoint_location",
        env_var="NITR_VERTEX_ENDPOINT_LOCATION",
    )

    aiplatform.init(project=config["project_id"], location=config["endpoint_location"])
    endpoint = aiplatform.Endpoint(
        endpoint_name=(
            f"projects/{config['project_id']}/locations/{config['endpoint_location']}"
            f"/endpoints/{config['endpoint_id']}"
        )
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
                call_qwen_vertex(endpoint, prompt, config)
            ),
            request_label="Qwen endpoint",
            error_label="Endpoint Error",
            response_delay_seconds=config["response_delay_seconds"],
            payload_error_message="No valid JSON payload found in the endpoint response.",
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
