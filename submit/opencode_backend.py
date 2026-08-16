"""Read-only OpenCode CLI adapter for the NITR submission pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import time
from pathlib import Path
from types import MappingProxyType

from backend_interface import Backend
from submit_common import (
    apply_file_replacements,
    extract_json_payload,
    prepare_output_dir,
    run_case_submission,
    save_response_text,
)


OPENCODE_PERMISSION = {
    "*": "deny",
    "read": "allow",
    "glob": "allow",
    "grep": "allow",
}
OPENCODE_DEFAULTS = {
    "model_name": None,
    "cli_timeout_seconds": 1800,
    "request_retry_attempts": 3,
    "request_retry_delay_seconds": 300.0,
}
OPENCODE_BACKEND_DEFAULTS = MappingProxyType(OPENCODE_DEFAULTS.copy())
FORBIDDEN_PROJECT_NAMES = {
    ".opencode",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTEXT.md",
    "opencode.json",
    "opencode.jsonc",
}
TRANSIENT_ERROR_MARKERS = (
    "429",
    "rate limit",
    "service unavailable",
    "temporarily unavailable",
    "too many requests",
)


class OpenCodeError(RuntimeError):
    """Base class for OpenCode adapter failures."""


class OpenCodeContractError(OpenCodeError):
    """A non-retryable response, isolation, or workspace contract failure."""


def transcript_output_path(response_output_path: str) -> str:
    """Return the raw OpenCode NDJSON transcript sidecar path."""
    if response_output_path.endswith(".txt"):
        return response_output_path[:-4] + ".transcript.jsonl"
    return response_output_path + ".transcript.jsonl"


def stderr_output_path(response_output_path: str) -> str:
    """Return the OpenCode stderr sidecar path."""
    if response_output_path.endswith(".txt"):
        return response_output_path[:-4] + ".stderr.txt"
    return response_output_path + ".stderr.txt"


def build_opencode_prompt(task_file: str) -> str:
    """Build the JSON-only prompt referencing a staged relative task path."""
    normalized = Path(task_file)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise OpenCodeContractError(f"Task path must be project-relative: {task_file}")
    task_path = normalized.as_posix()
    return f"""Complete the task described in ./{task_path}.

Read whatever project files you need to understand the repository.
Do not modify files directly and do not run shell commands.

Return only one JSON object with this exact shape:
{{
  "files": [
    {{
      "filename": "relative/path/to/file",
      "content": "full replacement file content"
    }}
  ]
}}

Include modified and newly created files.
Use project-relative paths.
Do not return diffs or partial patches.
Do not include markdown fences, explanations, or text outside the JSON object."""


def build_opencode_command(
    working_dir: str, prompt: str, model_name: str | None
) -> list[str]:
    """Construct the non-interactive OpenCode argv."""
    command = [
        "opencode",
        "--pure",
        "run",
        "--format",
        "json",
        "--agent",
        "build",
        "--dir",
        os.path.realpath(working_dir),
    ]
    if model_name:
        command.extend(["--model", model_name])
    command.append(prompt)
    return command


def validate_opencode_case_preflight(project_dir: str) -> None:
    """Reject case-owned OpenCode configuration and instruction surfaces."""
    root = Path(project_dir)
    for current_root, directories, files in os.walk(root, followlinks=False):
        relative_root = Path(current_root).relative_to(root)
        entries = [*directories, *files]
        for name in entries:
            if name in FORBIDDEN_PROJECT_NAMES:
                relative = (relative_root / name).as_posix()
                raise OpenCodeContractError(
                    f"OpenCode-specific config or instruction file is not allowed: {relative}"
                )
        directories[:] = [
            name for name in directories if not (Path(current_root) / name).is_symlink()
        ]


def snapshot_project_tree(project_dir: str) -> dict[str, tuple[str, int, str]]:
    """Snapshot files, directories, and symlinks without following symlinks."""
    root = Path(project_dir)
    snapshot: dict[str, tuple[str, int, str]] = {}
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                if directory == root and entry.name == ".git":
                    continue
                path = Path(entry.path)
                relative = path.relative_to(root).as_posix()
                metadata = os.lstat(path)
                mode = stat.S_IMODE(metadata.st_mode)
                if stat.S_ISREG(metadata.st_mode):
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    snapshot[relative] = ("file", mode, digest)
                elif stat.S_ISDIR(metadata.st_mode):
                    snapshot[relative] = ("directory", mode, "")
                    pending.append(path)
                elif stat.S_ISLNK(metadata.st_mode):
                    snapshot[relative] = ("symlink", mode, os.readlink(path))
                else:
                    raise OpenCodeContractError(
                        f"Unsupported special filesystem entry: {relative}"
                    )
    return snapshot


def changed_snapshot_paths(
    before: dict[str, tuple[str, int, str]],
    after: dict[str, tuple[str, int, str]],
) -> list[str]:
    """Return sorted paths whose presence, type, mode, or contents changed."""
    return sorted(
        path
        for path in before.keys() | after.keys()
        if before.get(path) != after.get(path)
    )


def extract_opencode_final_text(ndjson_text: str) -> str:
    """Decode the final root-session assistant message from OpenCode NDJSON."""
    root_session: str | None = None
    text_parts: dict[str, list[str]] = {}
    last_message_id: str | None = None
    known_events = {
        "step_start",
        "step_finish",
        "tool_use",
        "text",
        "reasoning",
        "error",
    }

    for line_number, raw_line in enumerate(ndjson_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise OpenCodeContractError(
                f"Malformed OpenCode NDJSON at line {line_number}: {error.msg}"
            ) from error
        if not isinstance(event, dict):
            raise OpenCodeContractError(
                f"OpenCode NDJSON line {line_number} must be an object"
            )
        session_id = event.get("sessionID")
        if not isinstance(session_id, str) or not session_id:
            raise OpenCodeContractError(
                f"OpenCode NDJSON line {line_number} has no valid sessionID"
            )
        if root_session is None:
            root_session = session_id
        elif session_id != root_session:
            # Child/subtask events must never become the NITR response. Ignore
            # their contents before validating root-session event shapes.
            continue

        event_type = event.get("type")
        if not isinstance(event_type, str):
            raise OpenCodeContractError(
                f"OpenCode NDJSON line {line_number} has no valid type"
            )
        if event_type not in known_events:
            continue
        if event_type == "error":
            raise OpenCodeContractError(
                f"OpenCode reported an error: {json.dumps(event.get('error'))}"
            )
        if event_type != "text":
            continue
        part = event.get("part")
        if not isinstance(part, dict):
            raise OpenCodeContractError(
                f"OpenCode text event at line {line_number} has no valid part"
            )
        message_id = part.get("messageID")
        text = part.get("text")
        if not isinstance(message_id, str) or not message_id:
            raise OpenCodeContractError(
                f"OpenCode text event at line {line_number} has no valid messageID"
            )
        if not isinstance(text, str):
            raise OpenCodeContractError(
                f"OpenCode text event at line {line_number} has no valid text"
            )
        text_parts.setdefault(message_id, []).append(text)
        last_message_id = message_id

    if last_message_id is None:
        raise OpenCodeContractError("OpenCode produced no final assistant text")
    final_text = "".join(text_parts[last_message_id]).strip()
    if not final_text:
        raise OpenCodeContractError("OpenCode produced empty final assistant text")
    return final_text


def normalize_process_output(value: str | bytes | None) -> str:
    """Normalize subprocess diagnostics, including TimeoutExpired byte output."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _copy_auth_file(data_dir: Path) -> None:
    """Copy only OpenCode's standard auth artifact into isolated data storage."""
    source_data = Path(
        os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
    )
    source = source_data / "opencode" / "auth.json"
    if not source.is_file():
        return
    target = data_dir / "opencode" / "auth.json"
    target.parent.mkdir(parents=True, mode=0o700)
    shutil.copyfile(source, target)
    os.chmod(target, 0o600)


def build_opencode_environment(temp_root: str) -> dict[str, str]:
    """Build an isolated, deny-by-default OpenCode subprocess environment."""
    root = Path(temp_root)
    home_dir = root / "home"
    config_dir = root / "config"
    opencode_config_dir = root / "opencode-config"
    data_dir = root / "data"
    cache_dir = root / "cache"
    state_dir = root / "state"
    for directory in (
        home_dir,
        config_dir,
        opencode_config_dir,
        data_dir,
        cache_dir,
        state_dir,
    ):
        directory.mkdir(parents=True, mode=0o700)
    _copy_auth_file(data_dir)

    environment = os.environ.copy()
    for name in (
        "OPENCODE_CONFIG",
        "OPENCODE_CONFIG_CONTENT",
        "OPENCODE_CONFIG_DIR",
        "OPENCODE_PERMISSION",
    ):
        environment.pop(name, None)
    inline_config = {
        "permission": OPENCODE_PERMISSION,
        "agent": {"build": {"permission": OPENCODE_PERMISSION}},
        "mcp": {},
        "lsp": False,
        "formatter": False,
        "share": "disabled",
    }
    environment.update(
        {
            "HOME": str(home_dir),
            "XDG_CONFIG_HOME": str(config_dir),
            "XDG_DATA_HOME": str(data_dir),
            "XDG_CACHE_HOME": str(cache_dir),
            "XDG_STATE_HOME": str(state_dir),
            "OPENCODE_CONFIG_DIR": str(opencode_config_dir),
            "OPENCODE_CONFIG_CONTENT": json.dumps(inline_config),
            "OPENCODE_PERMISSION": json.dumps(OPENCODE_PERMISSION),
            "OPENCODE_DISABLE_PROJECT_CONFIG": "1",
            "OPENCODE_DISABLE_CLAUDE_CODE": "1",
            "OPENCODE_DISABLE_DEFAULT_PLUGINS": "1",
            "OPENCODE_DISABLE_LSP_DOWNLOAD": "1",
            "OPENCODE_DISABLE_AUTOUPDATE": "1",
        }
    )
    return environment


def initialize_git_boundary(project_dir: str, temp_root: str) -> None:
    """Create a fresh Git discovery boundary without user/system configuration."""
    empty_config = Path(temp_root) / "gitconfig"
    empty_config.touch(mode=0o600)
    template_dir = Path(temp_root) / "git-template"
    template_dir.mkdir(mode=0o700)
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(empty_config),
            "GIT_TEMPLATE_DIR": str(template_dir),
        }
    )
    try:
        completed = subprocess.run(
            ["git", "init", "--quiet"],
            cwd=project_dir,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise OpenCodeError(
            "git is required to initialize the OpenCode workspace"
        ) from error
    if completed.returncode != 0:
        raise OpenCodeError(
            f"Could not initialize isolated Git workspace: {completed.stderr.strip()}"
        )


def _has_semantic_events(stdout: str) -> bool:
    """Return whether a stream contains assistant reasoning or text events."""
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("type") in {"text", "reasoning"}:
            return True
    return False


def is_retryable_transport_failure(stdout: str, stderr: str) -> bool:
    """Allow only explicit transient failures before semantic model output."""
    if _has_semantic_events(stdout):
        return False
    details = f"{stdout}\n{stderr}".lower()
    return any(marker in details for marker in TRANSIENT_ERROR_MARKERS)


def _save_transport_artifacts(
    response_output_path: str, stdout: str, stderr: str
) -> None:
    save_response_text(stdout, transcript_output_path(response_output_path))
    save_response_text(stderr, stderr_output_path(response_output_path))


def call_opencode(
    *,
    persistent_input: str,
    prompt: str,
    model_name: str | None,
    response_output_path: str,
    config: dict[str, object],
) -> str:
    """Run OpenCode in fresh isolated workspaces with bounded transport retries."""
    attempts = int(config["request_retry_attempts"])
    for attempt in range(1, attempts + 1):
        with tempfile.TemporaryDirectory(prefix="nitr-opencode-") as temp_root:
            project_dir = os.path.join(temp_root, "project")
            shutil.copytree(persistent_input, project_dir, symlinks=True)
            initialize_git_boundary(project_dir, temp_root)
            before = snapshot_project_tree(project_dir)
            environment = build_opencode_environment(temp_root)
            command = build_opencode_command(project_dir, prompt, model_name)
            started = time.time()
            try:
                completed = subprocess.run(
                    command,
                    cwd=os.path.realpath(project_dir),
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=float(config["cli_timeout_seconds"]),
                    check=False,
                )
                stdout = completed.stdout or ""
                stderr = completed.stderr or ""
            except subprocess.TimeoutExpired as error:
                stdout = normalize_process_output(error.stdout)
                stderr = normalize_process_output(error.stderr)
                _save_transport_artifacts(response_output_path, stdout, stderr)
                after = snapshot_project_tree(project_dir)
                changed = changed_snapshot_paths(before, after)
                if changed:
                    raise OpenCodeContractError(
                        "OpenCode modified its read-only workspace: "
                        + ", ".join(changed)
                    ) from error
                raise OpenCodeError("opencode CLI timed out") from error
            except FileNotFoundError as error:
                raise OpenCodeError(
                    "opencode CLI not found. Install and authenticate OpenCode, then "
                    "ensure `opencode` is on PATH."
                ) from error

            _save_transport_artifacts(response_output_path, stdout, stderr)
            after = snapshot_project_tree(project_dir)
            changed = changed_snapshot_paths(before, after)
            if changed:
                raise OpenCodeContractError(
                    "OpenCode modified its read-only workspace: " + ", ".join(changed)
                )
            if completed.returncode != 0:
                if attempt < attempts and is_retryable_transport_failure(
                    stdout, stderr
                ):
                    delay = float(config["request_retry_delay_seconds"])
                    print(
                        f"[!] Transient OpenCode failure on attempt {attempt}/{attempts}; "
                        f"retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                    continue
                details = stderr.strip() or stdout.strip()
                raise OpenCodeError(
                    f"opencode exited {completed.returncode}: {details[:500]}"
                )
            final_text = extract_opencode_final_text(stdout)
            print(f"[*] OpenCode completed in {time.time() - started:.1f}s")
            return final_text
    raise OpenCodeError("OpenCode failed without a response")


def run_opencode_cli(args) -> None:
    """Run submissions through a read-only local OpenCode CLI."""
    config: dict[str, object] = OPENCODE_DEFAULTS.copy()
    if args.model_name:
        config["model_name"] = args.model_name

    def run_single_task(
        input_project_dir: str,
        output_project_dir: str,
        task_file: str,
        response_output_path: str,
    ) -> bool:
        prepare_output_dir(input_project_dir, output_project_dir)
        try:
            validate_opencode_case_preflight(output_project_dir)
            task_path = os.path.join(output_project_dir, task_file)
            if not os.path.isfile(task_path):
                raise OpenCodeContractError(f"Staged task file not found: {task_file}")
            final_text = call_opencode(
                persistent_input=output_project_dir,
                prompt=build_opencode_prompt(task_file),
                model_name=config["model_name"],
                response_output_path=response_output_path,
                config=config,
            )
            save_response_text(final_text, response_output_path)
            payload = extract_json_payload(final_text)
            if not payload:
                raise OpenCodeContractError(
                    "No valid JSON payload found in the OpenCode response"
                )
            apply_file_replacements(payload, output_project_dir)
            print("[*] Patched project copy created successfully.")
            return True
        except Exception as error:
            print(f"[!] OpenCode CLI Error: {error}")
            return False

    run_case_submission(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        case_id=args.case_id,
        run_single_task=run_single_task,
        start_step=args.start_step or 1,
        end_step=args.end_step,
        run_label=(
            f"{args.run_label} (OpenCode CLI agent)"
            if getattr(args, "run_label", None)
            else "(OpenCode CLI agent)"
        ),
    )


class OpenCodeBackend(Backend):
    """OpenCode CLI implementation of the common backend interface."""

    name = "opencode-cli"
    defaults = OPENCODE_BACKEND_DEFAULTS

    def run(self, args) -> None:
        """Run an OpenCode CLI submission."""
        run_opencode_cli(args)
