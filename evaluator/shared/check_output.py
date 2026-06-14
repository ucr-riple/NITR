import json
import sys
from typing import Any, Iterable, NoReturn, TextIO
from enum import IntEnum


CHECK_PASSED = 0
CHECK_FAILED = 1


class RunResult(IntEnum):
    """Standard subprocess exit-code conventions."""

    SUCCESS = 0
    FAILED = 1
    COMMAND_NOT_FOUND = 127


def emit_check_result(*, passed: bool, findings: Iterable[Any], **extra: Any) -> int:
    """Emit the standard evaluator result payload and return a process code."""
    payload = {
        "passed": passed,
        "findings": list(findings),
        **extra,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    return CHECK_PASSED if passed else CHECK_FAILED


def fail_message(message: str) -> int:
    """Emit a one-finding failure result."""
    return emit_check_result(passed=False, findings=[message])


def die_message(
    message: str, *, code: int = CHECK_FAILED, stream: TextIO = sys.stdout
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
