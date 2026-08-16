"""Qwen through Vertex OpenAPI submission backend."""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request

from submit_common import require_config_value, run_case_submission, run_json_task


QWEN_OPENAPI_DEFAULTS = {
    "project_id": os.environ.get("NITR_GCP_PROJECT"),
    "region": os.environ.get("NITR_GCP_REGION", "global"),
    "model_name": "qwen/qwen3-coder-480b-a35b-instruct-maas",
    "response_delay_seconds": 60.0,
    "request_timeout_seconds": 1800.0,
    "request_retry_attempts": 3,
    "request_retry_delay_seconds": 300.0,
    "max_tokens": 16384,
    "temperature": 0.1,
    "top_p": 0.95,
}


def get_gcloud_access_token() -> str:
    """Fetch a short-lived bearer token for the OpenAPI request."""
    completed = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        check=True,
        capture_output=True,
        text=True,
    )
    token = completed.stdout.strip()
    if not token:
        raise ValueError("gcloud returned an empty access token")
    return token


def build_qwen_openapi_url(project_id: str, region: str) -> str:
    """Build the regional OpenAPI chat completions endpoint URL."""
    return (
        "https://aiplatform.googleapis.com/v1/projects/"
        f"{project_id}/locations/{region}/endpoints/openapi/chat/completions"
    )


def extract_qwen_openapi_text(payload: dict[str, object]) -> str:
    """Extract assistant text from a chat completions response."""
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
            text = first.get("text")
            if isinstance(text, str):
                return text
    raise ValueError("OpenAPI response did not contain choices[0].message.content")


def call_qwen_openapi(prompt: str, config: dict[str, object]) -> str:
    """Submit one OpenAPI chat request with the legacy retry policy."""
    payload = {
        "model": config["model_name"],
        "stream": False,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": config["max_tokens"],
        "temperature": config["temperature"],
        "top_p": config["top_p"],
    }
    url = build_qwen_openapi_url(str(config["project_id"]), str(config["region"]))
    attempts = int(config["request_retry_attempts"])
    last_error = None
    for attempt in range(1, attempts + 1):
        started = time.time()
        print(
            f"[*] Request attempt {attempt}/{attempts} started at "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(started))}"
        )
        try:
            token = get_gcloud_access_token()
            request = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(
                request, timeout=float(config["request_timeout_seconds"])
            ) as response:
                raw_text = response.read().decode("utf-8")
            response_payload = json.loads(raw_text)
            print(
                f"[*] Request attempt {attempt}/{attempts} succeeded in "
                f"{time.time() - started:.1f}s"
            )
            return extract_qwen_openapi_text(response_payload)
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(f"Status code:{error.code}, response:{body}")
        except Exception as error:
            last_error = error
        print(
            f"[!] Request attempt {attempt}/{attempts} failed after "
            f"{time.time() - started:.1f}s: {last_error}"
        )
        if attempt == attempts:
            raise last_error
        delay = float(config["request_retry_delay_seconds"])
        print(f"[*] Sleeping {delay:.1f}s before retry...")
        time.sleep(delay)
    raise RuntimeError(f"Request failed without a response: {last_error}")


def run_qwen_openapi(args) -> None:
    """Run submissions through Vertex's OpenAPI chat completions surface."""
    config: dict[str, object] = QWEN_OPENAPI_DEFAULTS.copy()
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

    def run_single_task(
        input_project_dir, output_project_dir, task_file, response_output_path
    ):
        return run_json_task(
            input_project_dir,
            output_project_dir,
            task_file,
            response_output_path,
            fetch_response=lambda _project_dir, prompt, _response_output_path: (
                call_qwen_openapi(prompt, config)
            ),
            request_label="Qwen3 Next 80B",
            error_label="OpenAPI Error",
            response_delay_seconds=config["response_delay_seconds"],
            payload_error_message="No valid JSON payload found in the OpenAPI response.",
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
