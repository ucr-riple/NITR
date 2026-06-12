#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
CASE_NAME="$(basename "$(cd "${SCRIPT_DIR}/.." && pwd)")"
CASE_ROOT="${REPO_ROOT}/cases/${CASE_NAME}"
EVALUATOR_ROOT="${REPO_ROOT}/evaluator/${CASE_NAME}"
export PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
BUILD_DIR="${BUILD_DIR:-${CASE_ROOT}/build-hidden}"
CMAKE_BIN="${CMAKE_BIN:-cmake}"
CTEST_BIN="${CTEST_BIN:-ctest}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
MODIFIED_FILES="${MODIFIED_FILES:-}"

log() {
  printf '[run_hidden] %s\n' "$*"
}

run_cmd() {
  log "$*"
  "$@"
}

run_check_allowed_file_touches() {
  if [[ -z "${MODIFIED_FILES}" ]]; then
    log 'Skipping check_allowed_file_touches.py (set MODIFIED_FILES="path1 path2 ..." to enable).'
    return 0
  fi

  # shellcheck disable=SC2206
  local files=( ${MODIFIED_FILES} )
  run_cmd "${PYTHON_BIN}" "${EVALUATOR_ROOT}/checks/check_allowed_file_touches.py" "${files[@]}"
}

main() {
  cd "${CASE_ROOT}" || exit 1

  run_cmd "${CMAKE_BIN}" -S . -B "${BUILD_DIR}" -DCASE015_ENABLE_VISIBLE_CHECKS=ON -DCASE015_ENABLE_HIDDEN_EVALUATOR=ON || exit 20
  run_cmd "${CMAKE_BIN}" --build "${BUILD_DIR}" || exit 21
  run_cmd "${CTEST_BIN}" --test-dir "${BUILD_DIR}" --output-on-failure || exit 22
  run_check_allowed_file_touches || exit 23

  log 'Hidden evaluator passed.'
}

main "$@"
