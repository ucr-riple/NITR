#!/usr/bin/env sh
set -eu

CLANG_FORMAT_BIN="${CLANG_FORMAT:-clang-format}"

if ! command -v "${CLANG_FORMAT_BIN}" >/dev/null 2>&1; then
  echo "error: clang-format not found. Set CLANG_FORMAT or install clang-format." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FILE_LIST="$(mktemp)"
FAIL_LIST="$(mktemp)"
FORMAT_OUTPUT="$(mktemp)"
trap 'rm -f "${FILE_LIST}" "${FAIL_LIST}" "${FORMAT_OUTPUT}"' EXIT HUP INT TERM

(
  cd "${ROOT_DIR}" &&
    git ls-files -- '*.h' '*.hh' '*.hpp' '*.hxx' '*.c' '*.cc' '*.cpp' '*.cxx' \
      ':(exclude)third_party/**'
) >"${FILE_LIST}"

FILE_COUNT="$(wc -l <"${FILE_LIST}" | tr -d ' ')"

if [ "${FILE_COUNT}" -eq 0 ]; then
  echo "No tracked C/C++ files found."
  exit 0
fi

cd "${ROOT_DIR}"
while IFS= read -r file; do
  [ -n "${file}" ] || continue
  "${CLANG_FORMAT_BIN}" "${file}" >"${FORMAT_OUTPUT}"
  if ! diff -u "${file}" "${FORMAT_OUTPUT}" >/dev/null 2>&1; then
    printf '%s\n' "${file}" >>"${FAIL_LIST}"
  fi
done <"${FILE_LIST}"

FAIL_COUNT="$(wc -l <"${FAIL_LIST}" | tr -d ' ')"

if [ "${FAIL_COUNT}" -gt 0 ]; then
  echo "clang-format check failed for ${FAIL_COUNT} file(s):"
  sed 's/^/  /' "${FAIL_LIST}"
  echo
  echo "Run tools/format.sh to apply formatting."
  exit 1
fi

echo "clang-format check passed."
