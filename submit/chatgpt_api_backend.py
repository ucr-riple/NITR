"""OpenAI Responses API submission backend."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from submit_common import (
    run_case_submission,
    run_json_task,
    save_json_payload,
    usage_output_path,
)


CHATGPT_API_DEFAULTS = {
    "model_name": "gpt-5-mini",
    "openai_api_base": os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
    "openai_api_key_env_var": "OPENAI_API_KEY",
    "response_delay_seconds": 15.0,
    "request_timeout_seconds": 1800.0,
    "request_retry_attempts": 3,
    "request_retry_delay_seconds": 300.0,
    "max_output_tokens": 32768,
}


def require_openai_api_key(env_var: str) -> str:
    """Load the configured OpenAI API key or fail clearly."""
    api_key = os.environ.get(env_var)
    if not api_key:
        raise EnvironmentError(f"{env_var} is not set")
    return api_key


def extract_openai_response_text(payload: dict[str, object]) -> str:
    """Normalize a Responses API payload into plain assistant text."""
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output_items = payload.get("output")
    if not isinstance(output_items, list):
        return ""
    chunks = []
    for item in output_items:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            text_value = content.get("text")
            if isinstance(text_value, str):
                chunks.append(text_value)
                continue
            if content.get("type") == "output_text":
                text_value = content.get("text")
                if isinstance(text_value, str):
                    chunks.append(text_value)
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def call_openai_responses_api(
    prompt: str, config: dict[str, object]
) -> tuple[str, dict[str, object]]:
    """Issue one Responses API request with the legacy retry policy."""
    api_key = require_openai_api_key(str(config["openai_api_key_env_var"]))
    endpoint = f"{str(config['openai_api_base']).rstrip('/')}/responses"
    attempts = int(config["request_retry_attempts"])
    last_error = None
    for attempt in range(1, attempts + 1):
        started = time.time()
        print(
            f"[*] Request attempt {attempt}/{attempts} started at "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(started))}"
        )
        try:
            payload = {
                "model": config["model_name"],
                "input": prompt,
                "max_output_tokens": config["max_output_tokens"],
            }
            request = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(
                request, timeout=float(config["request_timeout_seconds"])
            ) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
            response_text = extract_openai_response_text(response_payload)
            if not response_text.strip():
                raise ValueError("OpenAI Responses API returned an empty output text")
            print(
                f"[*] Request attempt {attempt}/{attempts} succeeded in "
                f"{time.time() - started:.1f}s"
            )
            return response_text, response_payload
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace").strip()
            last_error = RuntimeError(f"HTTP {error.code}: {body or error.reason}")
        except urllib.error.URLError as error:
            last_error = RuntimeError(f"Network error: {error.reason}")
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


def run_chatgpt_api(args) -> None:
    """Run submissions through the OpenAI Responses API backend."""
    config: dict[str, object] = CHATGPT_API_DEFAULTS.copy()
    if args.model_name:
        config["model_name"] = args.model_name

    def run_single_task(
        input_project_dir, output_project_dir, task_file, response_output_path
    ):
        def fetch_response(_project_dir, prompt, _response_output_path):
            response_text, response_payload = call_openai_responses_api(prompt, config)
            save_json_payload(
                response_payload,
                response_output_path.replace(".txt", ".api_response.json"),
            )
            save_json_payload(
                response_payload.get("usage", {}),
                usage_output_path(response_output_path),
            )
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
