import json
import os
import re
import shutil
import time


def resolve_cases_root(input_dir):
    """Accept either the repo root or a direct cases directory and normalize to cases/."""
    repo_cases_dir = os.path.join(input_dir, "cases")
    if os.path.isdir(repo_cases_dir):
        return repo_cases_dir
    if os.path.isdir(input_dir):
        return input_dir
    raise FileNotFoundError(f"Cases root not found under: {input_dir}")


def find_case_dir(cases_root, case_id):
    """Resolve a case id to the single matching case directory under the cases root."""
    prefix = f"{case_id}."
    matches = [
        entry for entry in os.listdir(cases_root)
        if entry.startswith(prefix) and os.path.isdir(os.path.join(cases_root, entry))
    ]
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected exactly one case directory for {case_id}, found: {matches}"
        )
    return os.path.join(cases_root, matches[0])


def ensure_parent_dir(path):
    """Create the parent directory for an output file if it does not exist yet."""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def load_case_granularity(repo_root, case_id):
    """Read the case granularity from the design matrix so submission flow can branch."""
    matrix_path = os.path.join(repo_root, "docs", "design_matrix.md")
    if not os.path.isfile(matrix_path):
        raise FileNotFoundError(f"design_matrix.md not found: {matrix_path}")

    pattern = re.compile(
        rf"^\|\s*{re.escape(case_id)}\s+[^|]*\|\s*[^|]*\|\s*(micro|multi-step)\s*\|$"
    )
    with open(matrix_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            match = pattern.match(line)
            if match:
                return match.group(1)

    raise ValueError(f"Granularity for case {case_id} not found in design_matrix.md")


def list_case_task_files(case_dir, granularity):
    """List the task files for a case, handling micro and multi-step layouts."""
    if granularity == "micro":
        task_path = os.path.join(case_dir, "TASK.md")
        if not os.path.isfile(task_path):
            raise FileNotFoundError(f"Micro case task file missing: {task_path}")
        return ["TASK.md"]

    task_files = []
    task_index = 1
    while True:
        task_name = f"TASK{task_index}.md"
        task_path = os.path.join(case_dir, task_name)
        if not os.path.isfile(task_path):
            break
        task_files.append(task_name)
        task_index += 1

    if not task_files:
        raise FileNotFoundError(
            f"No TASK1.md/TASK2.md/... files found for multi-step case: {case_dir}"
        )
    return task_files


def collect_project_data(project_dir, task_file):
    """Collect the source context that should be shown to the model for one task."""
    context = []
    valid_exts = (".cpp", ".h", ".cc", ".hpp", ".cmake", ".cu", ".txt")
    ignore_dirs = {"build", ".git", "bin", "obj"}
    selected_task_relpath = os.path.normpath(task_file)

    print(f"[*] Scanning project directory: {project_dir}")
    print(f"[*] Using task file: {selected_task_relpath}")
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), project_dir)

            should_include = file.endswith(valid_exts)
            if file.endswith(".md"):
                is_selected_task = os.path.normpath(rel_path) == selected_task_relpath
                is_other_task = (
                    re.fullmatch(r"TASK\d*\.md", file) is not None and not is_selected_task
                )
                should_include = is_selected_task or (
                    not is_other_task and file == "README.md"
                )

            if not should_include:
                continue

            try:
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    context.append(f"--- FILE: {rel_path} ---\n{f.read()}\n")
            except Exception as e:
                print(f"[-] Skipping {rel_path}: {e}")
    return "\n".join(context)


def extract_json_payload(response_text):
    """Parse the model response into a JSON object, tolerating light wrapper text."""
    fenced_match = re.search(r"```json\s*\n(.*?)\n```", response_text, re.DOTALL)
    candidate = fenced_match.group(1).strip() if fenced_match else response_text.strip()
    if not candidate:
        return None

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None

    try:
        return json.loads(candidate[start : end + 1])
    except json.JSONDecodeError:
        return None


def apply_file_replacements(payload, output_dir, allow_empty=False):
    """Validate the returned file list and write full-file replacements into the copy."""
    if not isinstance(payload, dict):
        raise ValueError("Response JSON must be an object")

    files = payload.get("files")
    if not isinstance(files, list):
        raise ValueError("Response JSON must contain a 'files' array")
    if not files:
        if allow_empty:
            print("[*] No files changed in this step.")
            return
        raise ValueError("Response JSON must contain a non-empty 'files' array")

    written_files = []
    for entry in files:
        if not isinstance(entry, dict):
            raise ValueError("Each file entry must be an object")

        filename = entry.get("filename")
        content = entry.get("content")
        if not isinstance(filename, str) or not filename:
            raise ValueError(
                "Each file entry must include a non-empty string 'filename'"
            )
        if not isinstance(content, str):
            raise ValueError("Each file entry must include string 'content'")

        normalized = os.path.normpath(filename)
        if os.path.isabs(normalized) or normalized.startswith(".."):
            raise ValueError(f"Invalid filename outside project: {filename}")

        full_path = os.path.join(output_dir, normalized)
        if os.path.exists(full_path) and not os.path.isfile(full_path):
            raise ValueError(f"Refusing to overwrite non-file path: {filename}")

        ensure_parent_dir(full_path)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        written_files.append(normalized)

    print(f"[+] Wrote files: {', '.join(written_files)}")


def prepare_output_dir(input_dir, output_dir):
    """Refresh the task workspace by copying the input project into a clean output dir."""
    if os.path.abspath(input_dir) == os.path.abspath(output_dir):
        raise ValueError("output_dir must be different from input_dir")

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    shutil.copytree(
        input_dir,
        output_dir,
        ignore=shutil.ignore_patterns(".git", "build", "bin", "obj", "__pycache__"),
    )
    print(f"[*] Copied project to output directory: {output_dir}")


def save_response_text(response_text, output_path):
    """Persist the raw model response for later inspection and debugging."""
    ensure_parent_dir(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response_text)
    print(f"[*] Saved raw response to: {output_path}")


def save_json_payload(payload, output_path):
    """Persist a JSON payload with stable formatting for downstream inspection."""
    ensure_parent_dir(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"[*] Saved JSON payload to: {output_path}")


def build_json_patch_prompt(project_context, task_file):
    """Build the strict JSON-only prompt contract used by most backends."""
    return f"""
    Context:
    {project_context}

    Task:
    Follow instructions in {task_file}.
    Return only one JSON object with this exact shape:
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
    Focus only on the implementation requested in {task_file}.
    """


def build_project_context_prompt(project_dir, task_file):
    """Assemble the model prompt after scanning the copied project workspace."""
    project_context = collect_project_data(project_dir, task_file)
    if not project_context:
        raise ValueError("No valid source files found in the copied project.")
    return build_json_patch_prompt(project_context, task_file)


def mirror_case_evaluator(repo_root, output_root, case_slug):
    """Copy the evaluator assets for the case into the output tree."""
    source_evaluator_dir = os.path.join(repo_root, "evaluator", case_slug)
    target_evaluator_dir = os.path.join(output_root, "evaluator", case_slug)
    if os.path.exists(target_evaluator_dir):
        shutil.rmtree(target_evaluator_dir)
    shutil.copytree(
        source_evaluator_dir,
        target_evaluator_dir,
        ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"),
    )
    print(f"[*] Mirrored evaluator to: {target_evaluator_dir}")


def copy_case_snapshot(source_dir, target_dir):
    """Replace the mirrored case snapshot with the latest staged project copy."""
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    shutil.copytree(
        source_dir,
        target_dir,
        ignore=shutil.ignore_patterns(
            ".git", "build", "bin", "obj", "__pycache__", ".DS_Store"
        ),
    )
    print(f"[*] Updated mirrored case directory: {target_dir}")


def run_json_task(
    input_project_dir,
    output_project_dir,
    task_file,
    response_output_path,
    *,
    fetch_response,
    request_label,
    error_label,
    response_delay_seconds=0.0,
    allow_empty_files=False,
    payload_error_message="No valid JSON payload found in the response.",
):
    """Run one task end-to-end: copy, prompt, fetch response, parse, and apply files."""
    source_task_path = os.path.join(input_project_dir, task_file)
    if not os.path.isfile(source_task_path):
        print(f"[!] Task file not found: {source_task_path}")
        return False

    prepare_output_dir(input_project_dir, output_project_dir)

    output_task_path = os.path.join(output_project_dir, task_file)
    if not os.path.isfile(output_task_path):
        print(f"[!] Task file not found in copied project: {output_task_path}")
        return False

    try:
        prompt = build_project_context_prompt(output_project_dir, task_file)
    except Exception as e:
        print(f"[!] {error_label}: {e}")
        return False

    request_started_at = time.time()
    request_started_label = time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime(request_started_at)
    )
    print(f"[*] Requesting {request_label} at {request_started_label}...")
    try:
        response_text = fetch_response(output_project_dir, prompt, response_output_path)
        total_elapsed_seconds = time.time() - request_started_at
        print(
            f"[*] {request_label} response received in {total_elapsed_seconds:.1f}s"
        )
        save_response_text(response_text, response_output_path)

        payload = extract_json_payload(response_text)
        if not payload:
            print(f"[-] {payload_error_message}")
            return False

        apply_file_replacements(
            payload, output_project_dir, allow_empty=allow_empty_files
        )
        if response_delay_seconds > 0:
            print(
                f"[*] Sleeping {response_delay_seconds:.1f}s after successful patch..."
            )
            time.sleep(response_delay_seconds)
        print("[*] Patched project copy created successfully.")
        return True
    except Exception as e:
        print(f"[!] {error_label}: {e}")
        return False


def run_case_submission(
    *,
    input_dir,
    output_dir,
    case_id,
    run_single_task,
    start_step=1,
    end_step=None,
    run_label=None,
):
    """Drive the full submission flow for one case across micro or multi-step layouts."""
    case_id = case_id.zfill(3)
    cases_root = resolve_cases_root(input_dir)
    repo_root = os.path.dirname(cases_root)
    case_dir = find_case_dir(cases_root, case_id)
    granularity = load_case_granularity(repo_root, case_id)
    task_files = list_case_task_files(case_dir, granularity)

    if start_step < 1:
        raise ValueError("--start_step must be >= 1")
    if end_step is not None and end_step < start_step:
        raise ValueError("--end_step must be >= --start_step")

    os.makedirs(output_dir, exist_ok=True)
    case_slug = os.path.basename(case_dir)
    mirrored_case_dir = os.path.join(output_dir, "cases", case_slug)
    response_dir = os.path.join(output_dir, "responses", case_slug)
    staging_root = os.path.join(output_dir, "staging", case_slug)
    mirror_case_evaluator(repo_root, output_dir, case_slug)

    label_suffix = f" {run_label}" if run_label else ""

    if granularity == "micro":
        if start_step != 1 or (end_step is not None and end_step != 1):
            raise ValueError("Micro cases only support step 1")
        print(f"[*] Running micro case {case_id}{label_suffix} from: {case_dir}")
        stage_output_dir = os.path.join(staging_root, "final")
        response_output_path = os.path.join(response_dir, "response.txt")
        success = run_single_task(
            case_dir, stage_output_dir, task_files[0], response_output_path
        )
        if not success:
            raise SystemExit(1)
        copy_case_snapshot(stage_output_dir, mirrored_case_dir)
        return

    print(f"[*] Running multi-step case {case_id}{label_suffix} from: {case_dir}")
    max_step = len(task_files)
    selected_end_step = end_step or max_step
    if start_step > max_step or selected_end_step > max_step:
        raise ValueError(f"Step range must be within 1..{max_step}")

    if start_step == 1:
        current_input_dir = case_dir
    else:
        current_input_dir = os.path.join(staging_root, f"step{start_step - 1}")
        if not os.path.isdir(current_input_dir):
            raise FileNotFoundError(
                f"Missing prior staged output for step {start_step - 1}: {current_input_dir}"
            )

    for step_index, task_file in enumerate(task_files, start=1):
        if step_index < start_step or step_index > selected_end_step:
            continue
        output_project_dir = os.path.join(staging_root, f"step{step_index}")
        response_output_path = os.path.join(
            response_dir, f"response_step{step_index}.txt"
        )
        print(f"[*] Running step {step_index} with {task_file}")
        success = run_single_task(
            current_input_dir,
            output_project_dir,
            task_file,
            response_output_path,
        )
        if not success:
            raise SystemExit(1)
        current_input_dir = output_project_dir

    copy_case_snapshot(current_input_dir, mirrored_case_dir)
