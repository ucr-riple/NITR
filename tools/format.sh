#!/usr/bin/env sh
set -eu

CLANG_FORMAT_BIN="${CLANG_FORMAT:-clang-format}"

if ! command -v "${CLANG_FORMAT_BIN}" >/dev/null 2>&1; then
  echo "error: clang-format not found. Set CLANG_FORMAT or install clang-format." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FILE_LIST="$(mktemp)"
trap 'rm -f "${FILE_LIST}"' EXIT HUP INT TERM

list_cpp_files() {
  (
    cd "${ROOT_DIR}" &&
      find . \
        \( -path './.git' -o -path './third_party' -o -path './build' -o -path './bin' -o -path './obj' \
           -o -path './__pycache__' -o -path './.submit-output' -o -path './submit-output' \) -prune \
        -o -type f \
        \( -name '*.h' -o -name '*.hh' -o -name '*.hpp' -o -name '*.hxx' \
           -o -name '*.c' -o -name '*.cc' -o -name '*.cpp' -o -name '*.cxx' \) \
        -print | sed 's#^\./##' | LC_ALL=C sort
  )
}

list_cpp_files >"${FILE_LIST}"

FILE_COUNT="$(wc -l <"${FILE_LIST}" | tr -d ' ')"

if [ "${FILE_COUNT}" -eq 0 ]; then
  echo "No C/C++ files found."
  exit 0
fi

echo "Formatting ${FILE_COUNT} C/C++ files with ${CLANG_FORMAT_BIN}..."
cd "${ROOT_DIR}"
while IFS= read -r file; do
  [ -n "${file}" ] || continue
  "${CLANG_FORMAT_BIN}" -i "${file}"
done <"${FILE_LIST}"

echo "clang-format completed."
