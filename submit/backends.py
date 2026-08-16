import json
import os
import subprocess
import time
import urllib.error
import urllib.request

from submit_common import (
    require_config_value,
    run_case_submission,
    run_json_task,
)

DEFAULTS = {
    # Qwen through a user-provided GCP Vertex endpoint. Requires endpoint id/location.
    "qwen-vertex": {
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
    },
    # Qwen through Vertex OpenAPI chat completions. Requires GCP project configuration.
    "qwen-openapi": {
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
    },
}


def run_qwen_vertex(args):
    """Run submissions against a user-managed Vertex endpoint that serves Qwen."""
    from google.cloud import aiplatform

    config = DEFAULTS["qwen-vertex"].copy()
    if args.project_id:
        config["project_id"] = args.project_id
    if args.endpoint_id:
        config["endpoint_id"] = args.endpoint_id
    if args.endpoint_location:
        config["endpoint_location"] = args.endpoint_location
    require_config_value(
        config,
        "project_id",
        cli_flag="--project_id",
        env_var="NITR_GCP_PROJECT",
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

    def build_prompt_payload(prompt):
        """Translate the prompt into the endpoint's configured request format."""
        if config["request_format"] == "chat":
            instances = [
                {
                    "@requestFormat": "chatCompletions",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": config["max_tokens"],
                    "temperature": config["temperature"],
                    "top_p": config["top_p"],
                    "top_k": config["top_k"],
                }
            ]
            parameters = None
        else:
            instances = [{"prompt": prompt}]
            parameters = {
                "max_tokens": config["max_tokens"],
                "temperature": config["temperature"],
                "top_p": config["top_p"],
                "top_k": config["top_k"],
            }
        return instances, parameters

    def extract_response_text(prediction):
        """Normalize a variety of Vertex prediction payload shapes into plain text."""
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
                            if isinstance(part, dict)
                            and isinstance(part.get("text"), str)
                        ]
                        if texts:
                            return "".join(texts)
            predictions = prediction.get("predictions")
            if isinstance(predictions, list) and predictions:
                return extract_response_text(predictions[0])
        if isinstance(prediction, list) and prediction:
            return extract_response_text(prediction[0])
        raise ValueError(
            f"Unsupported endpoint prediction payload shape: {type(prediction).__name__}"
        )

    aiplatform.init(project=config["project_id"], location=config["endpoint_location"])
    endpoint = aiplatform.Endpoint(
        endpoint_name=(
            f"projects/{config['project_id']}/locations/{config['endpoint_location']}"
            f"/endpoints/{config['endpoint_id']}"
        )
    )

    def call_endpoint(prompt):
        """Call the configured Vertex endpoint with retry and timeout handling."""
        instances, parameters = build_prompt_payload(prompt)
        last_error = None
        for attempt in range(1, config["request_retry_attempts"] + 1):
            started = time.time()
            print(
                f"[*] Request attempt {attempt}/{config['request_retry_attempts']} started at "
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
                    f"[*] Request attempt {attempt}/{config['request_retry_attempts']} "
                    f"succeeded in {time.time() - started:.1f}s"
                )
                return extract_response_text(first_prediction)
            except Exception as e:
                last_error = e
                print(
                    f"[!] Request attempt {attempt}/{config['request_retry_attempts']} failed after "
                    f"{time.time() - started:.1f}s: {e}"
                )
                if attempt == config["request_retry_attempts"]:
                    raise
                print(
                    f"[*] Sleeping {config['request_retry_delay_seconds']:.1f}s before retry..."
                )
                time.sleep(config["request_retry_delay_seconds"])
        raise RuntimeError(f"Request failed without a response: {last_error}")

    def run_single_task(
        input_project_dir, output_project_dir, task_file, response_output_path
    ):
        """Execute one task through the Qwen Vertex endpoint."""
        return run_json_task(
            input_project_dir,
            output_project_dir,
            task_file,
            response_output_path,
            fetch_response=lambda _project_dir, prompt, _response_output_path: (
                call_endpoint(prompt)
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


def run_qwen_openapi(args):
    """Run submissions through Vertex's OpenAPI chat completions surface."""
    config = DEFAULTS["qwen-openapi"].copy()
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

    def get_access_token():
        """Fetch a short-lived bearer token from gcloud for the OpenAPI request."""
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

    def build_endpoint_url():
        """Build the regional OpenAPI chat completions endpoint URL."""
        return (
            "https://aiplatform.googleapis.com/v1/projects/"
            f"{config['project_id']}/locations/{config['region']}/endpoints/openapi/chat/completions"
        )

    def extract_response_text(payload):
        """Extract assistant text from the OpenAPI chat completions response."""
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

    def call_openapi_chat(prompt):
        """Submit one OpenAPI chat request with retry handling around HTTP failures."""
        payload = {
            "model": config["model_name"],
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": config["max_tokens"],
            "temperature": config["temperature"],
            "top_p": config["top_p"],
        }
        url = build_endpoint_url()
        last_error = None
        for attempt in range(1, config["request_retry_attempts"] + 1):
            started = time.time()
            print(
                f"[*] Request attempt {attempt}/{config['request_retry_attempts']} started at "
                f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(started))}"
            )
            try:
                token = get_access_token()
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
                    request, timeout=config["request_timeout_seconds"]
                ) as response:
                    raw_text = response.read().decode("utf-8")
                response_payload = json.loads(raw_text)
                print(
                    f"[*] Request attempt {attempt}/{config['request_retry_attempts']} "
                    f"succeeded in {time.time() - started:.1f}s"
                )
                return extract_response_text(response_payload)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                last_error = RuntimeError(f"Status code:{e.code}, response:{body}")
            except Exception as e:
                last_error = e
            print(
                f"[!] Request attempt {attempt}/{config['request_retry_attempts']} failed after "
                f"{time.time() - started:.1f}s: {last_error}"
            )
            if attempt == config["request_retry_attempts"]:
                raise last_error
            print(
                f"[*] Sleeping {config['request_retry_delay_seconds']:.1f}s before retry..."
            )
            time.sleep(config["request_retry_delay_seconds"])
        raise RuntimeError(f"Request failed without a response: {last_error}")

    def run_single_task(
        input_project_dir, output_project_dir, task_file, response_output_path
    ):
        """Execute one task through the Qwen OpenAPI backend."""
        return run_json_task(
            input_project_dir,
            output_project_dir,
            task_file,
            response_output_path,
            fetch_response=lambda _project_dir, prompt, _response_output_path: (
                call_openapi_chat(prompt)
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


BACKEND_RUNNERS = {
    "qwen-vertex": run_qwen_vertex,
    "qwen-openapi": run_qwen_openapi,
}
