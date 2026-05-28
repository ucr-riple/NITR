import json
import os
import subprocess
import time
import urllib.error
import urllib.request

from submit_common import (
    apply_file_replacements,
    collect_project_data,
    extract_json_payload,
    prepare_output_dir,
    run_case_submission,
    run_json_task,
    save_json_payload,
    save_response_text,
)


DEFAULTS = {
    # OpenAI local CLI workflow. Requires the `codex` CLI on PATH.
    "chatgpt-codex": {
        "model_name": "gpt-5.4",
        "response_delay_seconds": 60.0,
        "request_timeout_seconds": 1800.0,
        "request_retry_attempts": 3,
        "request_retry_delay_seconds": 300.0,
    },
    # OpenAI official API workflow. Requires OPENAI_API_KEY.
    "chatgpt-api": {
        "model_name": "gpt-5-mini",
        "openai_api_base": os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
        "openai_api_key_env_var": "OPENAI_API_KEY",
        "response_delay_seconds": 15.0,
        "request_timeout_seconds": 1800.0,
        "request_retry_attempts": 3,
        "request_retry_delay_seconds": 300.0,
        "max_output_tokens": 32768,
    },
    # Anthropic via GCP Vertex integration. Requires GCP project configuration.
    "claude-vertex": {
        "project_id": os.environ.get("NITR_GCP_PROJECT"),
        "region": os.environ.get("NITR_GCP_REGION", "global"),
        "model_name": "claude-opus-4-5@20251101",
        "response_delay_seconds": 60.0,
        "request_timeout_seconds": 1800.0,
        "request_retry_attempts": 3,
        "request_retry_delay_seconds": 300.0,
        "max_tokens": 32768,
    },
    # Anthropic local CLI workflow. Requires the `claude` CLI on PATH.
    "claude-cli": {
        "model_name": "claude-opus-4-6",
        "cli_timeout_seconds": 1800,
        "request_retry_attempts": 3,
        "request_retry_delay_seconds": 300.0,
        "response_delay_seconds": 10.0,
        "allowed_tools": "Read",
    },
    # Gemini via GCP Vertex SDK. Requires GCP project configuration.
    "gemini-vertex": {
        "project_id": os.environ.get("NITR_GCP_PROJECT"),
        "region": os.environ.get("NITR_GCP_REGION", "global"),
        "model_name": "gemini-3.1-pro-preview",
        "response_delay_seconds": 60.0,
        "request_timeout_ms": 1800000,
        "request_retry_attempts": 3,
        "request_retry_delay_seconds": 300.0,
    },
    # Gemini local CLI workflow. Requires the `gemini` CLI on PATH.
    "gemini-cli": {
        "model_name": "gemini-3.1-pro-preview",
        "response_delay_seconds": 0.0,
    },
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


def transcript_output_path(response_output_path):
    """Derive the sidecar transcript filename for a saved backend response."""
    if response_output_path.endswith(".txt"):
        return response_output_path[:-4] + ".transcript.txt"
    return response_output_path + ".transcript.txt"


def usage_output_path(response_output_path):
    """Derive the sidecar usage filename for a saved backend response."""
    if response_output_path.endswith(".txt"):
        return response_output_path[:-4] + ".usage.json"
    return response_output_path + ".usage.json"


def require_openai_api_key(env_var):
    """Load the configured OpenAI API key or fail with a clear environment error."""
    api_key = os.environ.get(env_var)
    if not api_key:
        raise EnvironmentError(f"{env_var} is not set")
    return api_key


def require_config_value(config, key, cli_flag=None, env_var=None):
    """Require a backend config value and explain how the caller can provide it."""
    value = config.get(key)
    if value:
        return value

    parts = [f"Missing required configuration: {key}"]
    if cli_flag:
        parts.append(f"pass {cli_flag}")
    if env_var:
        parts.append(f"or set {env_var}")
    raise ValueError(", ".join(parts))


def extract_openai_response_text(payload):
    """Normalize the Responses API payload into plain assistant text."""
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


def extract_codex_usage_from_events(stdout_text):
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


def run_chatgpt_api(args):
    """Run submissions through the OpenAI Responses API backend."""
    config = DEFAULTS["chatgpt-api"].copy()
    if args.model_name:
        config["model_name"] = args.model_name

    def call_openai(prompt):
        """Issue one prompt to the Responses API with retry and usage capture."""
        last_error = None
        api_key = require_openai_api_key(config["openai_api_key_env_var"])
        endpoint = f"{config['openai_api_base'].rstrip('/')}/responses"

        for attempt in range(1, config["request_retry_attempts"] + 1):
            started = time.time()
            print(
                f"[*] Request attempt {attempt}/{config['request_retry_attempts']} started at "
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
                    request, timeout=config["request_timeout_seconds"]
                ) as response:
                    response_payload = json.loads(response.read().decode("utf-8"))
                response_text = extract_openai_response_text(response_payload)
                if not response_text.strip():
                    raise ValueError("OpenAI Responses API returned an empty output text")
                print(
                    f"[*] Request attempt {attempt}/{config['request_retry_attempts']} "
                    f"succeeded in {time.time() - started:.1f}s"
                )
                return response_text, response_payload
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace").strip()
                last_error = RuntimeError(f"HTTP {e.code}: {body or e.reason}")
            except urllib.error.URLError as e:
                last_error = RuntimeError(f"Network error: {e.reason}")
            except Exception as e:
                last_error = e

            print(
                f"[!] Request attempt {attempt}/{config['request_retry_attempts']} failed after "
                f"{time.time() - started:.1f}s: {last_error}"
            )
            if attempt == config["request_retry_attempts"]:
                raise last_error
            print(f"[*] Sleeping {config['request_retry_delay_seconds']:.1f}s before retry...")
            time.sleep(config["request_retry_delay_seconds"])

        raise RuntimeError(f"Request failed without a response: {last_error}")

    def run_single_task(input_project_dir, output_project_dir, task_file, response_output_path):
        """Execute one case task and persist both raw text and API metadata."""
        def fetch_response(_project_dir, prompt, _response_output_path):
            """Wrap the API call so run_json_task can stay backend-agnostic."""
            response_text, response_payload = call_openai(prompt)
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
    )


def run_chatgpt_codex(args):
    """Run submissions through the local Codex CLI in read-only mode."""
    config = DEFAULTS["chatgpt-codex"].copy()
    if args.model_name:
        config["model_name"] = args.model_name

    def call_codex(project_dir, prompt, temp_output_path):
        """Invoke codex exec and read the final assistant message plus usage metadata."""
        last_error = None
        for attempt in range(1, config["request_retry_attempts"] + 1):
            started = time.time()
            print(
                f"[*] Request attempt {attempt}/{config['request_retry_attempts']} started at "
                f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(started))}"
            )
            try:
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)
                completed = subprocess.run(
                    [
                        "codex",
                        "exec",
                        "--model",
                        config["model_name"],
                        "--sandbox",
                        "read-only",
                        "--skip-git-repo-check",
                        "-C",
                        project_dir,
                        "--json",
                        "--output-last-message",
                        temp_output_path,
                        "-",
                    ],
                    input=prompt,
                    text=True,
                    capture_output=True,
                    timeout=config["request_timeout_seconds"],
                    check=False,
                )
                if completed.returncode != 0:
                    stderr = completed.stderr.strip()
                    stdout = completed.stdout.strip()
                    details = stderr or stdout or f"codex exec exited with {completed.returncode}"
                    raise RuntimeError(details)
                if not os.path.isfile(temp_output_path):
                    raise ValueError("codex exec did not produce an output-last-message file")
                with open(temp_output_path, "r", encoding="utf-8") as f:
                    response_text = f.read()
                os.remove(temp_output_path)
                if not response_text.strip():
                    raise ValueError("codex exec produced an empty last message")
                print(
                    f"[*] Request attempt {attempt}/{config['request_retry_attempts']} "
                    f"succeeded in {time.time() - started:.1f}s"
                )
                return response_text, extract_codex_usage_from_events(completed.stdout)
            except Exception as e:
                last_error = e
                print(
                    f"[!] Request attempt {attempt}/{config['request_retry_attempts']} failed after "
                    f"{time.time() - started:.1f}s: {e}"
                )
                if attempt == config["request_retry_attempts"]:
                    raise
                print(f"[*] Sleeping {config['request_retry_delay_seconds']:.1f}s before retry...")
                time.sleep(config["request_retry_delay_seconds"])
        raise RuntimeError(f"Request failed without a response: {last_error}")

    def run_single_task(input_project_dir, output_project_dir, task_file, response_output_path):
        """Execute one task through Codex and apply the returned JSON patch."""
        def fetch_response(project_dir, prompt, _response_output_path):
            """Provide run_json_task with a backend-specific response fetcher."""
            response_text, usage_payload = call_codex(
                project_dir,
                prompt,
                os.path.join(project_dir, ".codex_last_message.txt"),
            )
            save_json_payload(
                usage_payload,
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
    )


def run_claude_vertex(args):
    """Run submissions through Anthropic's Vertex-hosted Claude API."""
    from anthropic import AnthropicVertex

    config = DEFAULTS["claude-vertex"].copy()
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

    def extract_message_text(message):
        """Flatten Claude content blocks into one plain-text response string."""
        parts = []
        for block in getattr(message, "content", []):
            text = getattr(block, "text", None)
            if isinstance(text, str) and text:
                parts.append(text)
        if not parts:
            raise ValueError("Claude response did not contain any text blocks")
        return "".join(parts)

    def call_claude(prompt):
        """Issue one Claude request with retry handling around Vertex failures."""
        last_error = None
        for attempt in range(1, config["request_retry_attempts"] + 1):
            started = time.time()
            print(
                f"[*] Request attempt {attempt}/{config['request_retry_attempts']} started at "
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
                    f"[*] Request attempt {attempt}/{config['request_retry_attempts']} "
                    f"succeeded in {time.time() - started:.1f}s"
                )
                return extract_message_text(message)
            except Exception as e:
                last_error = e
                print(
                    f"[!] Request attempt {attempt}/{config['request_retry_attempts']} failed after "
                    f"{time.time() - started:.1f}s: {e}"
                )
                if attempt == config["request_retry_attempts"]:
                    raise
                print(f"[*] Sleeping {config['request_retry_delay_seconds']:.1f}s before retry...")
                time.sleep(config["request_retry_delay_seconds"])
        raise RuntimeError(f"Request failed without a response: {last_error}")

    def run_single_task(input_project_dir, output_project_dir, task_file, response_output_path):
        """Execute one task through Claude Vertex using the shared JSON workflow."""
        return run_json_task(
            input_project_dir,
            output_project_dir,
            task_file,
            response_output_path,
            fetch_response=lambda _project_dir, prompt, _response_output_path: call_claude(prompt),
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
    )


def run_claude_cli(args):
    """Run submissions through the local Claude Code CLI."""
    config = DEFAULTS["claude-cli"].copy()
    if args.model_name:
        config["model_name"] = args.model_name

    def build_cli_prompt(task_file):
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

    def call_cli(prompt, working_dir, response_output_path):
        """Invoke the Claude CLI, saving both stdout and a combined transcript."""
        cmd = [
            "claude",
            "-p",
            prompt,
            "--model",
            config["model_name"],
            "--allowedTools",
            config["allowed_tools"],
            "--output-format",
            "text",
        ]
        last_error = None
        for attempt in range(1, config["request_retry_attempts"] + 1):
            started = time.time()
            print(
                f"[*] CLI attempt {attempt}/{config['request_retry_attempts']} started at "
                f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(started))}"
            )
            try:
                result = subprocess.run(
                    cmd,
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=config["cli_timeout_seconds"],
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
                        f"[!] CLI attempt {attempt} exited with code {result.returncode} after {elapsed:.1f}s"
                    )
                    print(f"    stderr: {stderr[:500]}")
                    last_error = RuntimeError(
                        f"claude exited {result.returncode}: {stderr[:200]}"
                    )
                    if attempt < config["request_retry_attempts"]:
                        print(
                            f"[*] Sleeping {config['request_retry_delay_seconds']:.1f}s before retry..."
                        )
                        time.sleep(config["request_retry_delay_seconds"])
                    continue
                print(
                    f"[*] CLI attempt {attempt}/{config['request_retry_attempts']} "
                    f"succeeded in {elapsed:.1f}s"
                )
                return stdout
            except subprocess.TimeoutExpired:
                elapsed = time.time() - started
                last_error = TimeoutError(f"claude CLI timed out after {elapsed:.1f}s")
                print(f"[!] CLI attempt {attempt} timed out after {elapsed:.1f}s")
                if attempt < config["request_retry_attempts"]:
                    print(
                        f"[*] Sleeping {config['request_retry_delay_seconds']:.1f}s before retry..."
                    )
                    time.sleep(config["request_retry_delay_seconds"])
            except FileNotFoundError:
                raise RuntimeError(
                    "claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
                )
        raise RuntimeError(f"All CLI attempts failed. Last error: {last_error}")

    def run_single_task(input_project_dir, output_project_dir, task_file, response_output_path):
        """Execute one task via Claude CLI and materialize the returned file set."""
        prepare_output_dir(input_project_dir, output_project_dir)
        prompt = build_cli_prompt(task_file)
        print(
            f"[*] Invoking Claude CLI at "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}..."
        )
        try:
            stdout = call_cli(prompt, output_project_dir, response_output_path)
            payload = extract_json_payload(stdout)
            if not payload:
                print("[-] No valid JSON payload found in the Claude CLI response.")
                return False
            apply_file_replacements(payload, output_project_dir)
            if config["response_delay_seconds"] > 0:
                print(
                    f"[*] Sleeping {config['response_delay_seconds']:.1f}s after successful patch..."
                )
                time.sleep(config["response_delay_seconds"])
            print("[*] Patched project copy created successfully.")
            return True
        except Exception as e:
            print(f"[!] CLI Error: {e}")
            return False

    run_case_submission(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        case_id=args.case_id,
        run_single_task=run_single_task,
        start_step=args.start_step or 1,
        end_step=args.end_step,
        run_label="(CLI agent)",
    )


def run_gemini_vertex(args):
    """Run submissions through the Gemini Vertex SDK backend."""
    from google import genai

    config = DEFAULTS["gemini-vertex"].copy()
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

    def call_gemini(prompt):
        """Generate one Gemini response with retries around transient API failures."""
        generate_config = genai.types.GenerateContentConfig(
            temperature=0.7,
            http_options={"timeout": config["request_timeout_ms"]},
        )
        response = None
        last_error = None
        for attempt in range(1, config["request_retry_attempts"] + 1):
            try:
                response = client.models.generate_content(
                    model=config["model_name"],
                    contents=prompt,
                    config=generate_config,
                )
                break
            except Exception as e:
                last_error = e
                print(
                    f"[!] Request attempt {attempt}/{config['request_retry_attempts']} failed: {e}"
                )
                if attempt == config["request_retry_attempts"]:
                    raise
                print(f"[*] Sleeping {config['request_retry_delay_seconds']:.1f}s before retry...")
                time.sleep(config["request_retry_delay_seconds"])
        if response is None:
            raise RuntimeError(f"Request failed without a response: {last_error}")
        return response.text

    def run_single_task(input_project_dir, output_project_dir, task_file, response_output_path):
        """Execute one task through Gemini Vertex using the shared JSON workflow."""
        return run_json_task(
            input_project_dir,
            output_project_dir,
            task_file,
            response_output_path,
            fetch_response=lambda _project_dir, prompt, _response_output_path: call_gemini(prompt),
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
    )


def run_gemini_cli(args):
    """Run submissions through the local Gemini CLI."""
    config = DEFAULTS["gemini-cli"].copy()
    if args.model_name:
        config["model_name"] = args.model_name

    def build_cli_prompt(project_dir, task_file):
        """Assemble the inline project context prompt required by the Gemini CLI."""
        project_context = collect_project_data(project_dir, task_file)
        if not project_context:
            raise ValueError("No valid source files found in the copied project.")
        return f"""
    Context:
    {project_context}

    Task:
    Follow instructions in {task_file}.

    IMPORTANT CONSTRAINTS:
    1. DO NOT use any tools to write or modify files directly.
    2. Return only one JSON object with this exact shape:
    {{
      "files": [
        {{
          "filename": "relative/path/to/file",
          "content": "full replacement file content"
        }}
      ]
    }}
    Include only the files you changed.
    Use project-relative file paths.
    Do not include explanations, markdown fences, or any text outside the JSON object.
    Do not return partial patches or diffs.
    """

    def run_single_task(input_project_dir, output_project_dir, task_file, response_output_path):
        """Execute one task via Gemini CLI and apply the emitted JSON patch."""
        prepare_output_dir(input_project_dir, output_project_dir)
        try:
            prompt = build_cli_prompt(output_project_dir, task_file)
        except Exception as e:
            print(f"[!] CLI Error: {e}")
            return False
        try:
            result = subprocess.run(
                ["gemini", "--model", config["model_name"]],
                input=prompt,
                text=True,
                capture_output=True,
                check=True,
            )
            response_text = result.stdout
            save_response_text(response_text, response_output_path)
            payload = extract_json_payload(response_text)
            if not payload:
                print("[-] No valid JSON payload found in the AI response.")
                print(f"[-] Raw snippet: {response_text[:300]}...")
                return False
            apply_file_replacements(payload, output_project_dir)
            if config["response_delay_seconds"] > 0:
                time.sleep(config["response_delay_seconds"])
            return True
        except subprocess.CalledProcessError as e:
            print(f"[!] CLI Execution Error:\n{e.stderr}")
            return False

    run_case_submission(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        case_id=args.case_id,
        run_single_task=run_single_task,
        start_step=args.start_step or 1,
        end_step=args.end_step,
    )


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
                            if isinstance(part, dict) and isinstance(part.get("text"), str)
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
                print(f"[*] Sleeping {config['request_retry_delay_seconds']:.1f}s before retry...")
                time.sleep(config["request_retry_delay_seconds"])
        raise RuntimeError(f"Request failed without a response: {last_error}")

    def run_single_task(input_project_dir, output_project_dir, task_file, response_output_path):
        """Execute one task through the Qwen Vertex endpoint."""
        return run_json_task(
            input_project_dir,
            output_project_dir,
            task_file,
            response_output_path,
            fetch_response=lambda _project_dir, prompt, _response_output_path: call_endpoint(prompt),
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
            print(f"[*] Sleeping {config['request_retry_delay_seconds']:.1f}s before retry...")
            time.sleep(config["request_retry_delay_seconds"])
        raise RuntimeError(f"Request failed without a response: {last_error}")

    def run_single_task(input_project_dir, output_project_dir, task_file, response_output_path):
        """Execute one task through the Qwen OpenAPI backend."""
        return run_json_task(
            input_project_dir,
            output_project_dir,
            task_file,
            response_output_path,
            fetch_response=lambda _project_dir, prompt, _response_output_path: call_openapi_chat(prompt),
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
    )


BACKEND_RUNNERS = {
    "chatgpt-codex": run_chatgpt_codex,
    "chatgpt-api": run_chatgpt_api,
    "claude-vertex": run_claude_vertex,
    "claude-cli": run_claude_cli,
    "gemini-vertex": run_gemini_vertex,
    "gemini-cli": run_gemini_cli,
    "qwen-vertex": run_qwen_vertex,
    "qwen-openapi": run_qwen_openapi,
}
