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
  -c 024
```

Note:

- `qwen-vertex` is the main exception; it is driven by `endpoint_id` and `endpoint_location` rather than `model_name`
- the default model values live in [`submit/backends.py`](submit/backends.py)

## 2. Required environment

At minimum, you need:

- Python 3
- the repository checked out locally
- whatever CLI tools or SDK credentials your chosen backend requires
- Docker, if you want the pinned Linux/GCC evaluator runtime

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

For Docker-backed runs, do not bake credentials into the image. Pass them at
runtime with host environment variables, `--docker-env-file`, or both.

### Docker image contract

The repository's Docker support is designed around a generic benchmark runtime,
not a backend-specific image.

The default image definition in `docker/nitr-linux-gcc.Dockerfile` gives you a
Linux/GCC baseline plus common shell tools. That is enough for API-backed
submit flows and for evaluator runs, but it does not bundle provider-specific
CLIs such as `codex`, `claude`, or `gemini`.

When you want a CLI-backed backend to run inside Docker, pass a compatible
custom image with `--docker-image`. A compatible image should provide:

- `python3` on `PATH`
- the benchmark baseline tools such as `bash`, `cmake`, `git`, and `rg`
- the backend-specific CLI on `PATH`
- runtime-injected credentials through env vars and/or bind mounts

The runtime mount/auth mechanism is generic:

- `--docker-env-file` passes env files through to `docker run`
- `--pass-env NAME` forwards selected host env vars
- `--docker-mount host:container[:options]` attaches config directories or credential files

## 3. Submit One Case

Use [`submit/submit_case.py`](submit/submit_case.py) for a single case.

Example:

```bash
python3 submit/submit_case.py \
  --backend chatgpt-codex \
  -i . \
  -o .submit-output/chatgpt-codex \
  -c 024
```

Example running submit inside Docker:

```bash
python3 submit/submit_case.py \
  --backend chatgpt-api \
  -i . \
  -o .submit-output/chatgpt-api \
  -c 024 \
  --runtime docker \
  --docker_build \
  --docker-env-file submit/docker.env.example
```

If your backend needs a custom CLI image, add `--docker-image <image>`.

Example with a model override:

```bash
python3 submit/submit_case.py \
  --backend chatgpt-api \
  --model_name gpt-5-mini \
  -i . \
  -o .submit-output/chatgpt-api \
  -c 024
```

To run the same case multiple times against a stochastic backend, set
`--submit-count`:

```bash
python3 submit/submit_case.py \
  --backend chatgpt-api \
  -i . \
  -o .submit-output/chatgpt-api \
  -c 024 \
  --submit-count 3
```

When `--submit-count` is greater than `1`, the tool keeps each attempt in a
separate subdirectory such as `.submit-output/chatgpt-api/run01/`,
`.submit-output/chatgpt-api/run02/`, and so on.
The same `run01/` structure is used when `--submit-count 1`.

You can use the same override pattern with other model-driven backends such as
`chatgpt-codex`, `claude-vertex`, `claude-cli`, `gemini-vertex`, `gemini-cli`,
and `qwen-openapi`.

For Docker-backed submit runs:

- `--runtime docker` moves the whole generation flow into the container
- known benchmark env vars are passed through automatically when set on the host
- `--pass-env NAME` adds extra env vars to `docker run`
- `--docker-env-file path` passes a Docker env-file through to `docker run`
- `--docker-mount host:container[:options]` attaches extra credential or config mounts

The generated output root will typically contain:

```text
.submit-output/<backend-name>/
`-- run01/
    |-- cases/
    |-- evaluator/
    |-- responses/
    |-- reports/
    `-- staging/
```

The `responses/` directory may also include sidecar metadata files such as:

- `*.usage.json` for token usage when the backend exposes it
- `*.api_response.json` for raw OpenAI Responses API payloads from `chatgpt-api`

## 4. Evaluate One Generated Case

Use [`submit/run_case_evaluator.py`](submit/run_case_evaluator.py) to evaluate one generated case.

Example:

```bash
python3 submit/run_case_evaluator.py \
  -g .submit-output/chatgpt-codex \
  -c 024 \
  -r . \
  --refresh_evaluator
```

Useful options:

- `--refresh_evaluator`: refresh evaluator files from the current repo before running
- `--build_timeout`: build timeout in seconds
- `--ctest_timeout`: functional test timeout in seconds
- `--check_timeout`: structural check timeout in seconds
- `--runtime docker`: run the evaluator inside Docker instead of the host machine
- `--docker_build`: build the pinned Linux/GCC image before running

Example with Docker:

```bash
python3 submit/run_case_evaluator.py \
  -g .submit-output/chatgpt-codex \
  -c 024 \
  -r . \
  --refresh_evaluator \
  --runtime docker \
  --docker_build
```

If `--generated-root` points at a backend directory containing `runXX/`,
the evaluator automatically scans all runs for that case and computes:

- `Pass@N`: `1` if at least one of the `N` runs passed
- `Stability`: `1` if all `N` runs are consistent (all pass or all fail)

Per-run reports remain under each `runXX/reports/`, and the aggregate case
report is written to `<generated-root>/reports/<case>.json`.

## 5. Run Batch Submit

Use [`submit/run_batch.sh`](submit/run_batch.sh) in submit mode.

Example:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend chatgpt-codex
```

Example with Docker:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend chatgpt-api \
  --submit-runtime docker \
  --docker-build \
  --docker-env-file submit/docker.env.example
```

Example with an explicit case list:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend qwen-openapi \
  --cases 001,002,024
```

Repeat batch submission multiple times per case:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend chatgpt-api \
  --cases 001,002,024 \
  --submit-count 3
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

Example with Docker:

```bash
bash submit/run_batch.sh \
  --mode evaluate \
  --generated-root .submit-output/chatgpt-codex \
  --runtime docker \
  --docker-build
```

When batch evaluation targets a backend root with `runXX/`, it also writes
`<generated-root>/reports/summary.json` containing per-case `Pass@N`,
`Stability`, and overall average rates.

Run both submit and evaluate in Docker:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend chatgpt-api \
  --runtime docker \
  --docker-build \
  --docker-env-file submit/docker.env.example
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

1. pick a case such as `024`
2. run `submit_case.py` for that backend
3. inspect files under `.submit-output/<backend>/responses/`
4. run `run_case_evaluator.py` for the generated case
5. if needed, scale up to `run_batch.sh`

## Notes

- The submit tooling assumes the standard NITR repository layout.
- Multi-step cases are driven automatically from `docs/design_matrix.md`.
- For the submit workflow implemented in this repository and used for
  paper-aligned reproduction, the coding agent sees the case directory plus only
  the TASK file for that step (`TASK.md` for single-step cases,
  `TASK1.md`/`TASK2.md`/... for multi-step cases).
- Under that protocol, `docs/<case>/SPEC.md` is not part of the agent-visible
  input.
- In multi-step runs, later steps continue from the previous step's generated
  code snapshot, but do not receive earlier `TASK*.md` files again.
- Backend-specific credentials are intentionally not stored in this repository.
- Docker evaluation is currently scoped to the Linux/GCC image shipped in this repo.
- The default Docker image is a generic runtime; use `--docker-image` when a backend needs a provider-specific CLI layer.
- For backend implementation details, see [`submit/README.md`](submit/README.md).

These notes describe the repository's submit/reproduction protocol. Other
external experiment setups are out of scope for this document.
