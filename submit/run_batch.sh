#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'EOF'
Usage:
  bash submit/run_batch.sh --mode submit --backend <backend> [options]
  bash submit/run_batch.sh --mode evaluate --generated-root <path> [options]

Submit mode options:
  --backend <name>            Backend for submit_case.py
  --output-root <path>        Output root for generated artifacts
  --cases <list>              Comma-separated case ids, or "all"
  --submit-count <n>          Number of independent submissions per case
  --model-name <name>         Optional model override for supported backends

Evaluate mode options:
  --generated-root <path>     Generated root containing cases/<case>

Common options:
  --log-file <path>           Log file path
  --build-timeout <sec>       Evaluator build timeout
  --ctest-timeout <sec>       Evaluator ctest timeout
  --check-timeout <sec>       Evaluator structural check timeout
  --runtime <local|docker>    Shared default runtime for submit/evaluate
  --submit-runtime <mode>     Runtime override for submit mode
  --evaluate-runtime <mode>   Runtime override for evaluate mode
  --docker-image <image>      Docker image for Docker-backed runs
  --docker-platform <plat>    Docker platform for Docker-backed runs
  --dockerfile <path>         Dockerfile used by --docker-build
  --docker-build              Build the Docker image before the first Docker-backed run
  --pass-env <name>           Extra env var name to pass into Docker; repeatable
  --docker-env-file <path>    Docker env-file to pass through; repeatable
  --docker-mount <spec>       Extra bind mount host:container[:options]; repeatable
EOF
}

default_output_root_for_backend() {
  case "$1" in
    chatgpt-codex) echo "${REPO_ROOT}/.submit-output/chatgpt-codex" ;;
    chatgpt-api) echo "${REPO_ROOT}/.submit-output/chatgpt-api" ;;
    claude-vertex) echo "${REPO_ROOT}/.submit-output/claude-vertex" ;;
    claude-cli) echo "${REPO_ROOT}/.submit-output/claude-cli" ;;
    gemini-vertex) echo "${REPO_ROOT}/.submit-output/gemini-vertex" ;;
    gemini-cli) echo "${REPO_ROOT}/.submit-output/gemini-cli" ;;
    qwen-vertex) echo "${REPO_ROOT}/.submit-output/qwen-vertex" ;;
    qwen-openapi) echo "${REPO_ROOT}/.submit-output/qwen-openapi" ;;
    *) echo "${REPO_ROOT}/.submit-output/${1}" ;;
  esac
}

default_cases_for_backend() {
  case "$1" in
    chatgpt-codex|chatgpt-api|claude-cli|qwen-openapi)
      echo "001,002,003,004,005,006,007,008,009,010,011,012,013,014,015,016,017,018,019,020,021,022,023,024"
      ;;
    claude-vertex)
      echo "008,009,010,011,012,013,014,015,016,017,018,019,020,021,022,023,024"
      ;;
    gemini-vertex)
      echo "006"
      ;;
    gemini-cli)
      echo "017"
      ;;
    qwen-vertex)
      echo "016,017,018,019,020,021,022,023,024"
      ;;
    *)
      echo "001,002,003,004,005,006,007,008,009,010,011,012,013,014,015,016,017,018,019,020,021,022,023,024"
      ;;
  esac
}

MODE=""
BACKEND=""
OUTPUT_ROOT=""
GENERATED_ROOT=""
LOG_FILE=""
CASES=""
MODEL_NAME=""
SUBMIT_COUNT=1
BUILD_TIMEOUT=300
CTEST_TIMEOUT=120
CHECK_TIMEOUT=60
RUNTIME="local"
SUBMIT_RUNTIME=""
EVALUATE_RUNTIME=""
DOCKER_IMAGE="nitr-linux-gcc:latest"
DOCKER_PLATFORM="linux/amd64"
DOCKERFILE="${REPO_ROOT}/docker/nitr-linux-gcc.Dockerfile"
DOCKER_BUILD=0
PASS_ENV_ARGS=()
DOCKER_ENV_FILE_ARGS=()
DOCKER_MOUNT_ARGS=()

require_value() {
  local option_name="$1"
  if [[ $# -lt 2 || -z "${2:-}" || "${2:-}" == --* ]]; then
    echo "${option_name} requires a value" >&2
    exit 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --backend)
      BACKEND="${2:-}"
      shift 2
      ;;
    --output-root)
      OUTPUT_ROOT="${2:-}"
      shift 2
      ;;
    --generated-root)
      GENERATED_ROOT="${2:-}"
      shift 2
      ;;
    --log-file)
      LOG_FILE="${2:-}"
      shift 2
      ;;
    --cases)
      CASES="${2:-}"
      shift 2
      ;;
    --model-name)
      MODEL_NAME="${2:-}"
      shift 2
      ;;
    --submit-count)
      require_value "$1" "${2:-}"
      SUBMIT_COUNT="${2:-}"
      shift 2
      ;;
    --build-timeout)
      BUILD_TIMEOUT="${2:-}"
      shift 2
      ;;
    --ctest-timeout)
      CTEST_TIMEOUT="${2:-}"
      shift 2
      ;;
    --check-timeout)
      CHECK_TIMEOUT="${2:-}"
      shift 2
      ;;
    --runtime)
      RUNTIME="${2:-}"
      shift 2
      ;;
    --submit-runtime)
      SUBMIT_RUNTIME="${2:-}"
      shift 2
      ;;
    --evaluate-runtime)
      EVALUATE_RUNTIME="${2:-}"
      shift 2
      ;;
    --docker-image)
      DOCKER_IMAGE="${2:-}"
      shift 2
      ;;
    --docker-platform)
      DOCKER_PLATFORM="${2:-}"
      shift 2
      ;;
    --dockerfile)
      DOCKERFILE="${2:-}"
      shift 2
      ;;
    --docker-build)
      DOCKER_BUILD=1
      shift
      ;;
    --pass-env)
      PASS_ENV_ARGS+=("--pass-env" "${2:-}")
      shift 2
      ;;
    --docker-env-file)
      DOCKER_ENV_FILE_ARGS+=("--docker-env-file" "${2:-}")
      shift 2
      ;;
    --docker-mount)
      DOCKER_MOUNT_ARGS+=("--docker-mount" "${2:-}")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${MODE}" ]]; then
  echo "--mode is required" >&2
  usage >&2
  exit 1
fi

SUBMIT_RUNTIME="${SUBMIT_RUNTIME:-${RUNTIME}}"
EVALUATE_RUNTIME="${EVALUATE_RUNTIME:-${RUNTIME}}"

if [[ "${MODE}" == "submit" ]]; then
  if [[ -z "${BACKEND}" ]]; then
    echo "--backend is required for submit mode" >&2
    exit 1
  fi

  OUTPUT_ROOT="${OUTPUT_ROOT:-$(default_output_root_for_backend "${BACKEND}")}"
  LOG_FILE="${LOG_FILE:-${REPO_ROOT}/.submit-output/logs/${BACKEND}_submit.log}"
  CASES="${CASES:-$(default_cases_for_backend "${BACKEND}")}"

  mkdir -p "$(dirname "${LOG_FILE}")"

  {
    submit_extra_args=(
      --runtime "${SUBMIT_RUNTIME}"
      --docker-image "${DOCKER_IMAGE}"
      --docker-platform "${DOCKER_PLATFORM}"
      --dockerfile "${DOCKERFILE}"
    )
    if [[ ${#PASS_ENV_ARGS[@]} -gt 0 ]]; then
      submit_extra_args+=("${PASS_ENV_ARGS[@]}")
    fi
    if [[ ${#DOCKER_ENV_FILE_ARGS[@]} -gt 0 ]]; then
      submit_extra_args+=("${DOCKER_ENV_FILE_ARGS[@]}")
    fi
    if [[ ${#DOCKER_MOUNT_ARGS[@]} -gt 0 ]]; then
      submit_extra_args+=("${DOCKER_MOUNT_ARGS[@]}")
    fi
    if [[ -n "${MODEL_NAME}" ]]; then
      submit_extra_args+=(--model-name "${MODEL_NAME}")
    fi
    if [[ "${DOCKER_BUILD}" == "1" && "${SUBMIT_RUNTIME}" == "docker" ]]; then
      submit_extra_args+=(--docker-build)
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting batch submit"
    echo "Repo root: ${REPO_ROOT}"
    echo "Backend: ${BACKEND}"
    echo "Output root: ${OUTPUT_ROOT}"
    echo "Python: ${PYTHON_BIN}"
    echo "Cases: ${CASES}"
    echo "Submit count: ${SUBMIT_COUNT}"
    echo "Runtime: ${SUBMIT_RUNTIME}"

    if ! [[ "${SUBMIT_COUNT}" =~ ^[1-9][0-9]*$ ]]; then
      echo "--submit-count must be a positive integer" >&2
      exit 1
    fi

    cd "${REPO_ROOT}"

    if [[ "${CASES}" == "all" ]]; then
      CASES="$(find cases -mindepth 1 -maxdepth 1 -type d | sort | xargs -n1 basename | cut -d. -f1 | paste -sd, -)"
      echo "Expanded cases: ${CASES}"
    fi

    IFS=',' read -r -a CASE_ARRAY <<< "${CASES}"
    failures=()

    for case_id in "${CASE_ARRAY[@]}"; do
      case_id="$(echo "${case_id}" | xargs)"
      [[ -z "${case_id}" ]] && continue
      echo "===== CASE ${case_id} ====="
      if "${PYTHON_BIN}" -u submit/submit_case.py \
        --backend "${BACKEND}" \
        -i . \
        -o "${OUTPUT_ROOT}" \
        -c "${case_id}" \
        --submit-count "${SUBMIT_COUNT}" \
        "${submit_extra_args[@]}"; then
        echo "===== CASE ${case_id} EXIT 0 ====="
        submit_extra_args=(
          --runtime "${SUBMIT_RUNTIME}"
          --docker-image "${DOCKER_IMAGE}"
          --docker-platform "${DOCKER_PLATFORM}"
          --dockerfile "${DOCKERFILE}"
        )
        if [[ ${#PASS_ENV_ARGS[@]} -gt 0 ]]; then
          submit_extra_args+=("${PASS_ENV_ARGS[@]}")
        fi
        if [[ ${#DOCKER_ENV_FILE_ARGS[@]} -gt 0 ]]; then
          submit_extra_args+=("${DOCKER_ENV_FILE_ARGS[@]}")
        fi
        if [[ ${#DOCKER_MOUNT_ARGS[@]} -gt 0 ]]; then
          submit_extra_args+=("${DOCKER_MOUNT_ARGS[@]}")
        fi
        if [[ -n "${MODEL_NAME}" ]]; then
          submit_extra_args+=(--model-name "${MODEL_NAME}")
        fi
      else
        exit_code=$?
        echo "===== CASE ${case_id} EXIT ${exit_code} ====="
        failures+=("${case_id}")
      fi
    done

    if [[ ${#failures[@]} -gt 0 ]]; then
      echo "Failed cases: ${failures[*]}"
      exit 1
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Batch submit finished"
  } 2>&1 | tee "${LOG_FILE}"

  exit 0
fi

if [[ "${MODE}" == "evaluate" ]]; then
  GENERATED_ROOT="${GENERATED_ROOT:-}"
  if [[ -z "${GENERATED_ROOT}" ]]; then
    echo "--generated-root is required for evaluate mode" >&2
    exit 1
  fi

  LOG_FILE="${LOG_FILE:-${REPO_ROOT}/.submit-output/logs/evaluator_batch.log}"
  mkdir -p "$(dirname "${LOG_FILE}")"

  {
    evaluator_extra_args=()
    if [[ "${DOCKER_BUILD}" == "1" && "${EVALUATE_RUNTIME}" == "docker" ]]; then
      evaluator_extra_args+=(--docker_build)
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting evaluator batch run"
    echo "Repo root: ${REPO_ROOT}"
    echo "Generated root: ${GENERATED_ROOT}"
    echo "Python: ${PYTHON_BIN}"
    echo "Runtime: ${EVALUATE_RUNTIME}"

    cd "${REPO_ROOT}"

    discover_case_names() {
      local root="$1"
      if [[ -d "${root}/cases" ]]; then
        find "${root}/cases" -mindepth 1 -maxdepth 1 -type d | sort | sed 's#.*/##'
        return
      fi
      find "${root}" -mindepth 3 -maxdepth 3 -type d -path '*/cases/*' | sort | sed 's#.*/##' | awk '!seen[$0]++'
    }

    CASE_NAMES=()
    while IFS= read -r case_name; do
      [[ -z "${case_name}" ]] && continue
      CASE_NAMES+=("${case_name}")
    done < <(discover_case_names "${GENERATED_ROOT}")
    if [[ ${#CASE_NAMES[@]} -eq 0 ]]; then
      echo "Generated cases not found under: ${GENERATED_ROOT}"
      exit 1
    fi

    evaluated_failures=()
    evaluation_errors=()
    for case_name in "${CASE_NAMES[@]}"; do
      case_id="${case_name%%.*}"
      report_path="${GENERATED_ROOT}/reports/${case_name}.json"
      exit_code=0
      evaluator_cmd=(
        "${PYTHON_BIN}" submit/run_case_evaluator.py
        -g "${GENERATED_ROOT}"
        -c "${case_id}"
        -r .
        --refresh-evaluator
        --runtime "${EVALUATE_RUNTIME}"
        --docker-image "${DOCKER_IMAGE}"
        --docker-platform "${DOCKER_PLATFORM}"
        --dockerfile "${DOCKERFILE}"
        --build-timeout "${BUILD_TIMEOUT}"
        --ctest-timeout "${CTEST_TIMEOUT}"
        --check-timeout "${CHECK_TIMEOUT}"
      )
      if [[ ${#PASS_ENV_ARGS[@]} -gt 0 ]]; then
        evaluator_cmd+=("${PASS_ENV_ARGS[@]}")
      fi
      if [[ ${#DOCKER_ENV_FILE_ARGS[@]} -gt 0 ]]; then
        evaluator_cmd+=("${DOCKER_ENV_FILE_ARGS[@]}")
      fi
      if [[ ${#DOCKER_MOUNT_ARGS[@]} -gt 0 ]]; then
        evaluator_cmd+=("${DOCKER_MOUNT_ARGS[@]}")
      fi
      if [[ ${#evaluator_extra_args[@]} -gt 0 ]]; then
        evaluator_cmd+=("${evaluator_extra_args[@]}")
      fi
      echo "===== CASE ${case_id} (${case_name}) ====="
      if "${evaluator_cmd[@]}"; then
        echo "===== CASE ${case_id} EXIT 0 ====="
      else
        exit_code=$?
        echo "===== CASE ${case_id} EXIT ${exit_code} ====="
        classification="$("${PYTHON_BIN}" - <<'PY' "${report_path}"
import json
import sys
from pathlib import Path

report_path = Path(sys.argv[1])
try:
    if not report_path.is_file():
        print("evaluation_error")
        raise SystemExit(0)

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if payload.get("evaluation_error") or payload.get("evaluation_errors", 0) > 0:
        print("evaluation_error")
    elif payload.get("passed") == False:
        print("evaluated_failure")
    elif payload.get("passed") == True:
        print("evaluated_success")
    else:
        print("evaluation_error")
except Exception:
    print("evaluation_error")
    raise SystemExit(0)
PY
)" || classification="evaluation_error"
        if [[ "${classification}" == "evaluated_failure" ]]; then
          evaluated_failures+=("${case_id}")
        else
          evaluation_errors+=("${case_id}")
        fi
      fi
      if [[ "${exit_code}" == "0" ]]; then
        evaluator_extra_args=()
      fi
    done

    if [[ ${#evaluated_failures[@]} -gt 0 ]]; then
      echo "Failed cases (evaluated but failed): ${evaluated_failures[*]}"
    fi

    if [[ ${#evaluation_errors[@]} -gt 0 ]]; then
      echo "Failed to evaluate: ${evaluation_errors[*]}"
    fi

    if [[ ${#evaluated_failures[@]} -gt 0 || ${#evaluation_errors[@]} -gt 0 ]]; then
      batch_exit_code=1
    else
      batch_exit_code=0
    fi

    summary_path="${GENERATED_ROOT}/reports/summary.json"
    "${PYTHON_BIN}" - <<'PY' "${GENERATED_ROOT}" "${summary_path}"
import json
import sys
from pathlib import Path

generated_root = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
reports_dir = generated_root / "reports"
case_reports = []
try:
    if reports_dir.is_dir():
        for report_path in sorted(reports_dir.glob("*.json")):
            if report_path.name == "summary.json":
                continue
            try:
                payload = json.loads(report_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if "case_slug" not in payload:
                continue
            submission_count = payload.get("submission_count", 1)
            pass_metric = payload.get("pass_at")
            if not isinstance(pass_metric, dict):
                pass_metric = {
                    "name": f"Pass@{submission_count}",
                    "n": submission_count,
                    "value": 1 if payload.get("passed") else 0,
                }
            stability_metric = payload.get("stability")
            if not isinstance(stability_metric, dict):
                stability_metric = {
                    "name": "Stability",
                    "n": submission_count,
                    "value": 1,
                }
            case_reports.append(
                {
                    "case_id": payload["case_id"],
                    "case_slug": payload["case_slug"],
                    "submission_count": submission_count,
                    "pass_at": pass_metric,
                    "stability": stability_metric,
                    "passed": bool(payload.get("passed")),
                    "report_path": str(report_path),
                }
            )

    pass_values = [report["pass_at"]["value"] for report in case_reports]
    stability_values = [report["stability"]["value"] for report in case_reports]
    submission_counts = sorted({report["submission_count"] for report in case_reports})

    summary = {
        "generated_root": str(generated_root),
        "total_cases": len(case_reports),
        "submission_counts": submission_counts,
        "cases": case_reports,
        "pass_rate": (
            sum(pass_values) / len(pass_values) if pass_values else 0.0
        ),
        "stability_rate": (
            sum(stability_values) / len(stability_values) if stability_values else 0.0
        ),
    }
    if len(submission_counts) == 1:
        n = submission_counts[0]
        summary["pass_metric_name"] = f"Pass@{n}"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[*] Saved aggregate batch summary to: {summary_path}")
except Exception as exc:
    print(f"[!] Failed to write aggregate batch summary: {exc}")
    raise SystemExit(0)
PY

    if [[ "${batch_exit_code}" == "1" ]]; then
      exit 1
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Evaluator batch run finished"
  } 2>&1 | tee "${LOG_FILE}"

  exit 0
fi

echo "Unsupported mode: ${MODE}" >&2
exit 1
