import re

from evaluator.shared.path_checks import case_root_from_script, read_text
from evaluator.shared.check_output import emit_check_result

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

    return emit_check_result(passed=not violations, findings=violations)


if __name__ == "__main__":
    raise SystemExit(main())
