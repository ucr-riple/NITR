# How to Submit

This document explains how to run NITR submissions locally with the tooling under `submit/`.

The submission workflow in this repository is:

1. choose a case
2. run one backend to generate edits under `.submit-output/`
3. evaluate the generated result with the public evaluator

This repository does not provide a hosted submission service. All submission runs are local.

## 1. Choose a backend

Single-case and batch submission both use the same backend names accepted by [`submit/submit_case.py`](submit/submit_case.py):

- `chatgpt-codex`
- `chatgpt-api`
- `claude-vertex`
- `claude-cli`
- `gemini-vertex`
- `gemini-cli`
- `qwen-vertex`
- `qwen-openapi`

Different backends may require different local dependencies or credentials.

Most backends also have a default `model_name`, but that value is only a default.
For backends that accept models directly, you can override it with `--model_name`.

Example:

```bash
python3 submit/submit_case.py \
  --backend gemini-vertex \
  --model_name gemini-2.5-pro \
  -i . \
  -o .submit-output/gemini-2.5-pro \
  -c 021
```

Note:

- `qwen-vertex` is the main exception; it is driven by `endpoint_id` and `endpoint_location` rather than `model_name`
- the default model values live in [`submit/backends.py`](submit/backends.py)

## 2. Required environment

At minimum, you need:

- Python 3
- the repository checked out locally
- whatever CLI tools or SDK credentials your chosen backend requires

### Python packages

The submit tooling has a small set of optional Python dependencies listed in
[`submit/requirements.txt`](submit/requirements.txt).

Recommended setup with `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -r submit/requirements.txt
```

Equivalent setup with `pip`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r submit/requirements.txt
```

Notes:

- `chatgpt-codex`, `chatgpt-api`, and `run_case_evaluator.py` mostly use the Python standard library
- Vertex-backed backends may require the packages in `submit/requirements.txt`
- CLI-backed backends may also require external CLI binaries in addition to Python packages

### CLI backends

Some submit backends require a locally installed CLI tool:

- `chatgpt-codex` requires the `codex` CLI
- `claude-cli` requires the `claude` CLI
- `gemini-cli` requires the `gemini` CLI

Before using those backends, make sure the corresponding command is available on `PATH`.

Quick checks:

```bash
codex --help
claude --help
gemini --help
```

If one of these commands is missing, install and authenticate that CLI first according to its official setup instructions before running `submit_case.py` or `run_batch.sh`.

Examples:

- `chatgpt-api` requires `OPENAI_API_KEY`
- Vertex-backed backends typically require `NITR_GCP_PROJECT`
- `qwen-vertex` may also require `NITR_VERTEX_ENDPOINT_ID` and `NITR_VERTEX_ENDPOINT_LOCATION`
- CLI-backed backends require the corresponding CLI binary to be installed and on `PATH`

Common environment variables used by the submit tooling:

```bash
export OPENAI_API_KEY=...
export NITR_GCP_PROJECT=...
export NITR_GCP_REGION=global
export NITR_VERTEX_ENDPOINT_ID=...
export NITR_VERTEX_ENDPOINT_LOCATION=...
```

## 3. Submit One Case

Use [`submit/submit_case.py`](submit/submit_case.py) for a single case.

Example:

```bash
python3 submit/submit_case.py \
  --backend chatgpt-codex \
  -i . \
  -o .submit-output/chatgpt-codex \
  -c 021
```

Example with a model override:

```bash
python3 submit/submit_case.py \
  --backend chatgpt-api \
  --model_name gpt-5-mini \
  -i . \
  -o .submit-output/chatgpt-api \
  -c 021
```

You can use the same override pattern with other model-driven backends such as
`chatgpt-codex`, `claude-vertex`, `claude-cli`, `gemini-vertex`, `gemini-cli`,
and `qwen-openapi`.

The generated output root will typically contain:

```text
.submit-output/<backend-name>/
|-- cases/
|-- evaluator/
|-- responses/
|-- reports/
`-- staging/
```

## 4. Evaluate One Generated Case

Use [`submit/run_case_evaluator.py`](submit/run_case_evaluator.py) to evaluate one generated case.

Example:

```bash
python3 submit/run_case_evaluator.py \
  -g .submit-output/chatgpt-codex \
  -c 021 \
  -r . \
  --refresh_evaluator
```

Useful options:

- `--refresh_evaluator`: refresh evaluator files from the current repo before running
- `--build_timeout`: build timeout in seconds
- `--ctest_timeout`: functional test timeout in seconds
- `--check_timeout`: structural check timeout in seconds

## 5. Run Batch Submit

Use [`submit/run_batch.sh`](submit/run_batch.sh) in submit mode.

Example:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend chatgpt-codex
```

Example with an explicit case list:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend qwen-openapi \
  --cases 001,002,021
```

If `--cases all` is used, the script expands to all case ids currently present under `cases/`.

## 6. Run Batch Evaluate

Use the same shell script in evaluate mode.

Example:

```bash
bash submit/run_batch.sh \
  --mode evaluate \
  --generated-root .submit-output/chatgpt-codex
```

You can also pass evaluator timeout overrides:

```bash
bash submit/run_batch.sh \
  --mode evaluate \
  --generated-root .submit-output/chatgpt-codex \
  --build-timeout 600 \
  --ctest-timeout 180 \
  --check-timeout 120
```

## 7. Recommended Workflow

For a typical local run:

1. pick a case such as `021`
2. run `submit_case.py` for that backend
3. inspect files under `.submit-output/<backend>/responses/`
4. run `run_case_evaluator.py` for the generated case
5. if needed, scale up to `run_batch.sh`

## Notes

- The submit tooling assumes the standard NITR repository layout.
- Multi-step cases are driven automatically from `docs/design_matrix.md`.
- Backend-specific credentials are intentionally not stored in this repository.
- For backend implementation details, see [`submit/README.md`](submit/README.md).
