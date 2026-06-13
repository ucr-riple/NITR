from pathlib import Path
import re
import sys

from evaluator.shared.path_checks import case_root_from_script, read_text

ROOT = case_root_from_script(__file__)
FILES = [
    ROOT / "src" / "report_renderer.h",
    ROOT / "src" / "report_renderer.cc",
]

SIGNATURE_RE = re.compile(r"^[^\n;{}]*\([^\n)]*\bcompact_mode\b[^\n)]*\)")

def main() -> int:
    violations = []
    for path in FILES:
        text = read_text(path, missing_ok=False)
        for match in SIGNATURE_RE.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            violations.append(
                f"{path.relative_to(ROOT)}:{line_no}: standalone compact_mode parameter in function signature"
            )

    if violations:
        print("[FAIL] detected compact_mode parameter sprawl:")
        for violation in violations:
            print(violation)
        return 1

    print("[PASS] no compact_mode parameter sprawl detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
