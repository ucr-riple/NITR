from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluator.shared.check_utils import case_root_from_script, read_text

ROOT = case_root_from_script(__file__)
FILES = [
    ROOT / "src" / "report_renderer.h",
    ROOT / "src" / "report_renderer.cc",
]

SIGNATURE_RE = re.compile(r"^[^\n;{}]*\([^\n)]*\bcompact_mode\b[^\n)]*\)")

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
    sys.exit(1)

print("[PASS] no compact_mode parameter sprawl detected")
