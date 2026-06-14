import json
import sys
from typing import Any, Iterable, NoReturn, TextIO


def emit_check_result(*, passed: bool, findings: Iterable[Any], **extra: Any) -> int:
    """Emit the standard evaluator result payload and return a process code."""
    payload = {
        "passed": passed,
        "findings": list(findings),
        **extra,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if passed else 1


def fail_message(message: str) -> int:
    """Emit a one-finding failure result."""
    return emit_check_result(passed=False, findings=[message])


def die_message(
    message: str, *, code: int = 1, stream: TextIO = sys.stdout
) -> NoReturn:
    """Emit a one-finding failure result and terminate immediately."""
    payload = json.dumps(
        {"passed": False, "findings": [message]},
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )
    print(payload, file=stream)
    raise SystemExit(code)
