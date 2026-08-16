"""Gemini CLI submission backend."""

from __future__ import annotations

import subprocess
import time

from submit_common import (
    apply_file_replacements,
    collect_project_data,
    extract_json_payload,
    prepare_output_dir,
    run_case_submission,
    save_response_text,
)


GEMINI_CLI_DEFAULTS = {
    "model_name": "gemini-3.1-pro-preview",
    "response_delay_seconds": 0.0,
}


def build_gemini_cli_command(model_name: str) -> list[str]:
    """Build the Gemini CLI command without invoking it."""
    return ["gemini", "--model", model_name]


def build_gemini_cli_prompt(project_dir: str, task_file: str) -> str:
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


def run_gemini_cli(args) -> None:
    """Run submissions through the local Gemini CLI."""
    config = GEMINI_CLI_DEFAULTS.copy()
    if args.model_name:
        config["model_name"] = args.model_name

    def run_single_task(
        input_project_dir, output_project_dir, task_file, response_output_path
    ):
        """Execute one task via Gemini CLI and apply the emitted JSON patch."""
        prepare_output_dir(input_project_dir, output_project_dir)
        try:
            prompt = build_gemini_cli_prompt(output_project_dir, task_file)
        except Exception as error:
            print(f"[!] CLI Error: {error}")
            return False
        try:
            result = subprocess.run(
                build_gemini_cli_command(config["model_name"]),
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
        except subprocess.CalledProcessError as error:
            print(f"[!] CLI Execution Error:\n{error.stderr}")
            return False

    run_case_submission(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        case_id=args.case_id,
        run_single_task=run_single_task,
        start_step=args.start_step or 1,
        end_step=args.end_step,
        run_label=getattr(args, "run_label", None),
    )
