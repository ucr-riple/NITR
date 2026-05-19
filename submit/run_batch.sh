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

Evaluate mode options:
  --generated-root <path>     Generated root containing cases/<case>

Common options:
  --log-file <path>           Log file path
  --build-timeout <sec>       Evaluator build timeout
  --ctest-timeout <sec>       Evaluator ctest timeout
  --check-timeout <sec>       Evaluator structural check timeout
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
BUILD_TIMEOUT=300
CTEST_TIMEOUT=120
CHECK_TIMEOUT=60

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
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting batch submit"
    echo "Repo root: ${REPO_ROOT}"
    echo "Backend: ${BACKEND}"
    echo "Output root: ${OUTPUT_ROOT}"
    echo "Python: ${PYTHON_BIN}"
    echo "Cases: ${CASES}"

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
        -c "${case_id}"; then
        echo "===== CASE ${case_id} EXIT 0 ====="
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
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting evaluator batch run"
    echo "Repo root: ${REPO_ROOT}"
    echo "Generated root: ${GENERATED_ROOT}"
    echo "Python: ${PYTHON_BIN}"

    cd "${REPO_ROOT}"
    if [[ ! -d "${GENERATED_ROOT}/cases" ]]; then
      echo "Generated cases directory not found: ${GENERATED_ROOT}/cases"
      exit 1
    fi

    evaluated_failures=()
    evaluation_errors=()
    while IFS= read -r case_dir; do
      case_name="$(basename "${case_dir}")"
      case_id="${case_name%%.*}"
      report_path="${GENERATED_ROOT}/reports/${case_name}.json"
      echo "===== CASE ${case_id} (${case_name}) ====="
      if "${PYTHON_BIN}" submit/run_case_evaluator.py \
        -g "${GENERATED_ROOT}" \
        -c "${case_id}" \
        -r . \
        --refresh_evaluator \
        --build_timeout "${BUILD_TIMEOUT}" \
        --ctest_timeout "${CTEST_TIMEOUT}" \
        --check_timeout "${CHECK_TIMEOUT}"; then
        echo "===== CASE ${case_id} EXIT 0 ====="
      else
        exit_code=$?
        echo "===== CASE ${case_id} EXIT ${exit_code} ====="
        if [[ -f "${report_path}" ]] && grep -q '"passed":[[:space:]]*false' "${report_path}"; then
          evaluated_failures+=("${case_id}")
        else
          evaluation_errors+=("${case_id}")
        fi
      fi
    done < <(find "${GENERATED_ROOT}/cases" -mindepth 1 -maxdepth 1 -type d | sort)

    if [[ ${#evaluated_failures[@]} -gt 0 ]]; then
      echo "Failed cases (evaluated but failed): ${evaluated_failures[*]}"
    fi

    if [[ ${#evaluation_errors[@]} -gt 0 ]]; then
      echo "Failed to evaluate: ${evaluation_errors[*]}"
    fi

    if [[ ${#evaluated_failures[@]} -gt 0 || ${#evaluation_errors[@]} -gt 0 ]]; then
      exit 1
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Evaluator batch run finished"
  } 2>&1 | tee "${LOG_FILE}"

  exit 0
fi

echo "Unsupported mode: ${MODE}" >&2
exit 1
