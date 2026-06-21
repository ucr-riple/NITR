# Submit Tooling

This directory contains local submission helpers for running NITR cases against different model backends and evaluating the generated outputs.

The submit tooling is organized into these components:

- `submit_case.py`: unified entrypoint that dispatches to a selected backend
- `backends.py` and `submit_common.py`: backend adapters and shared submission logic
- `run_case_evaluator.py`: copy one generated case into a clean NITR workspace, build it, run CTest, and then run structural checks
- `../docker/nitr-linux-gcc.Dockerfile`: pinned Linux/GCC evaluator image definition
- `docker.env.example`: sample env-file for Docker-backed submit/evaluate runs

Batch helper:

- `run_batch.sh`: unified shell entrypoint for batch submit and batch evaluate

## Docker Model

The Docker support in this repository is intentionally split into two layers:

- benchmark runtime: a Linux/GCC baseline plus common shell tooling
- agent image: any container image that also contains the backend-specific CLI or SDK setup you want to use

The repository ships one default benchmark runtime image definition at
[`../docker/nitr-linux-gcc.Dockerfile`](../docker/nitr-linux-gcc.Dockerfile).
It is meant to be generic, not provider-specific.

If you want to run a CLI-backed backend such as `chatgpt-codex`,
`claude-cli`, or `gemini-cli` inside Docker, point `--docker-image` at an
image that satisfies this contract:

- `python3` is available on `PATH`
- the NITR baseline tools are available, such as `bash`, `cmake`, `git`, and `rg`
- the backend-specific CLI is available on `PATH`
- credentials are injected at runtime through env vars and/or bind mounts, not baked into the image

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
`-- run01/
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

Run the same case multiple times to sample backend randomness:

```bash
python3 submit/submit_case.py \
  --backend chatgpt-api \
  -i . \
  -o .submit-output/chatgpt-api \
  -c 024 \
  --submit-count 3
```

When `--submit-count` is greater than `1`, outputs are written under
`run01/`, `run02/`, and so on beneath the requested output root.
The same `run01/` layout is also used when `--submit-count 1`.

Run one case fully inside Docker:

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

You can swap the image with `--docker-image` if a backend needs additional
tools or authentication helpers beyond the default runtime image.

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

If the generated root is a backend root that contains `runXX/` subdirectories,
`run_case_evaluator.py` evaluates every run for the requested case and writes:

- per-run reports under `runXX/reports/<case>.json`
- an aggregate case report under `reports/<case>.json`

The aggregate report includes:

- `Pass@N`: `1` if at least one of `N` runs passed, else `0`
- `Stability`: `1` if all `N` runs agree (all pass or all fail), else `0`

Evaluate one generated case inside the pinned Linux/GCC container:

```bash
python3 submit/run_case_evaluator.py \
  -g .submit-output/chatgpt-codex \
  -c 024 \
  -r . \
  --refresh_evaluator \
  --runtime docker \
  --docker_build
```

Docker-backed runs automatically pass through the common benchmark credential
variables when they are set on the host, and you can add more with
`--pass-env <NAME>` or `--docker-env-file <path>`.

For file-backed credentials or CLI config directories, use
`--docker-mount host_path:container_path[:options]`.

Run the evaluator over all generated cases in one output root:

```bash
bash submit/run_batch.sh \
  --mode evaluate \
  --generated-root .submit-output/chatgpt-codex
```

When `--generated-root` points at a backend root containing `runXX/`,
batch evaluation aggregates per-case metrics across runs and also writes
`reports/summary.json` with per-case `Pass@N` / `Stability` plus overall rates.

Run batch evaluation inside the same Docker image:

```bash
bash submit/run_batch.sh \
  --mode evaluate \
  --generated-root .submit-output/chatgpt-codex \
  --runtime docker \
  --docker-build
```

Run batch submit for one backend:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend chatgpt-codex
```

Run batch submit in Docker:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend chatgpt-api \
  --submit-runtime docker \
  --docker-build \
  --docker-env-file submit/docker.env.example
```

Run batch submit with an explicit case list:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend qwen-openapi \
  --cases 001,002,024
```

Run batch submit with repeated attempts per case:

```bash
bash submit/run_batch.sh \
  --mode submit \
  --backend chatgpt-api \
  --cases 001,002 \
  --submit-count 3
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
- The default Docker image is a generic benchmark runtime, not a provider-specific agent image.
- CLI-backed backends can run in Docker when `--docker-image` points at an image that provides the required CLI and runtime auth inputs.
- Docker-based evaluation currently targets `linux/amd64` with GCC.
- No personal project IDs, endpoint IDs, or local interpreter paths are stored in the repository. Pass them with CLI flags or environment variables such as `NITR_GCP_PROJECT`, `NITR_GCP_REGION`, `NITR_VERTEX_ENDPOINT_ID`, and `NITR_VERTEX_ENDPOINT_LOCATION` when needed.

This README documents the submit behavior implemented in this repository and
used for paper-aligned reproduction. It does not attempt to cover other
possible external experiment protocols.
