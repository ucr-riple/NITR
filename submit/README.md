# Submit Tooling

This directory contains local submission helpers for running NITR cases against different model backends and evaluating the generated outputs.

The submit tooling is organized into these components:

- `submit_case.py`: unified entrypoint that dispatches to a selected backend
- `backends.py` and `submit_common.py`: backend adapters and shared submission logic
- `run_case_evaluator.py`: copy one generated case into a clean NITR workspace, build it, run CTest, and then run structural checks

Batch helper:

- `run_batch.sh`: unified shell entrypoint for batch submit and batch evaluate

## Python Environment

Optional Python dependencies for backend integrations are listed in
[`requirements.txt`](requirements.txt).

Setup with `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -r submit/requirements.txt
```

Setup with `pip`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r submit/requirements.txt
```

## CLI Prerequisites

Some backends require external CLI tools in addition to Python packages:

- `chatgpt-codex` requires `codex`
- `claude-cli` requires `claude`
- `gemini-cli` requires `gemini`

Verify availability with:

```bash
codex --help
claude --help
gemini --help
```

## Output layout

By default, the shell wrapper writes outputs under:

```text
.submit-output/<backend-name>/
```

Typical generated structure:

```text
.submit-output/<backend-name>/
|-- cases/
|-- evaluator/
|-- responses/
|-- reports/
`-- staging/
```

Response sidecars may also appear under `responses/`, for example:

- `*.usage.json`: token usage metadata when the backend exposes it
- `*.api_response.json`: raw OpenAI Responses API payloads for `chatgpt-api`

## Common usage

Run one case through the unified submit entrypoint:

```bash
python3 submit/submit_case.py \
  --backend chatgpt-codex \
  -i . \
  -o .submit-output/chatgpt-codex \
  -c 024
```

Most model-driven backends expose a default `model_name`, but you can override
it with `--model_name`.

Example with a model override:

```bash
python3 submit/submit_case.py \
  --backend chatgpt-api \
  --model_name gpt-5-mini \
  -i . \
  -o .submit-output/chatgpt-api \
  -c 024
```

This applies to backends such as `chatgpt-codex`, `chatgpt-api`,
`claude-vertex`, `claude-cli`, `gemini-vertex`, `gemini-cli`, and
`qwen-openapi`.

For usage accounting:

- `chatgpt-api` writes the API `usage` object to `responses/*.usage.json`
- `chatgpt-codex` writes best-effort usage metadata from `codex exec --json` to `responses/*.usage.json`

`qwen-vertex` is the main exception because it is configured through
`endpoint_id` and `endpoint_location` instead of `model_name`.

Evaluate one generated case:

```bash
python3 submit/run_case_evaluator.py -g .submit-output/chatgpt-codex -c 024 -r . --refresh_evaluator
```

Run the evaluator over all generated cases in one output root:

```bash
bash submit/run_batch.sh \
  --mode evaluate \
  --generated-root .submit-output/chatgpt-codex
```

Run batch submit for one backend:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend chatgpt-codex
```

Run batch submit with an explicit case list:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend qwen-openapi \
  --cases 001,002,024
```

## Notes

- The submit scripts assume the standard NITR layout with `cases/`, `docs/`, and `evaluator/`.
- Multi-step cases are driven by `TASK1.md`, `TASK2.md`, and so on based on `docs/design_matrix.md`.
- In the repository's submit flow, the model context includes the case project
  files plus only the currently selected `TASK.md` / `TASK*.md` file for that
  step.
- `docs/<case>/SPEC.md` is not included in the agent-visible input.
- For multi-step cases, later steps continue from the previous step's staged
  code output, but earlier `TASK*.md` files are not re-exposed in later steps.
- Some backends require external credentials or installed CLIs.
- No personal project IDs, endpoint IDs, or local interpreter paths are stored in the repository. Pass them with CLI flags or environment variables such as `NITR_GCP_PROJECT`, `NITR_GCP_REGION`, `NITR_VERTEX_ENDPOINT_ID`, and `NITR_VERTEX_ENDPOINT_LOCATION` when needed.

This README documents the submit behavior implemented in this repository and
used for paper-aligned reproduction. It does not attempt to cover other
possible external experiment protocols.
