#!/usr/bin/env sh
set -eu

if [ -n "${RUFF:-}" ]; then
  RUFF_CMD="${RUFF}"
elif command -v ruff >/dev/null 2>&1; then
  RUFF_CMD="ruff"
elif python3 -m ruff --version >/dev/null 2>&1; then
  RUFF_CMD="python3 -m ruff"
else
  echo "error: ruff not found. Set RUFF or install ruff." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FILE_LIST="$(mktemp)"
trap 'rm -f "${FILE_LIST}"' EXIT HUP INT TERM

list_python_files() {
  (
    cd "${ROOT_DIR}" &&
      find ./evaluator ./submit ./tools \
        -type f \
        -name '*.py' \
        -print | sed 's#^\./##' | LC_ALL=C sort
  )
}

list_python_files >"${FILE_LIST}"

FILE_COUNT="$(wc -l <"${FILE_LIST}" | tr -d ' ')"

if [ "${FILE_COUNT}" -eq 0 ]; then
  echo "No Python files found."
  exit 0
fi

cd "${ROOT_DIR}"
if ! xargs ${RUFF_CMD} format --check <"${FILE_LIST}"; then
  echo
  echo "Run tools/format_python.sh to apply formatting."
  exit 1
fi

echo "ruff format check passed."
