"""Canonical registry for NITR submission backends."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

import backends as legacy_backends
from backend_interface import Backend
from claude_cli_backend import CLAUDE_CLI_DEFAULTS, run_claude_cli
from codex_cli_backend import CODEX_CLI_DEFAULTS, run_chatgpt_codex
from gemini_cli_backend import GEMINI_CLI_DEFAULTS, run_gemini_cli
from opencode_backend import OPENCODE_DEFAULTS, run_opencode_cli


BackendRunner = Callable[[argparse.Namespace], None]


@dataclass(frozen=True, eq=False)
class FunctionBackend(Backend):
    """Adapt an existing function-based backend to the common interface."""

    name: str
    runner: BackendRunner
    defaults: Mapping[str, object] = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "defaults", MappingProxyType(dict(self.defaults)))

    def run(self, args: argparse.Namespace) -> None:
        """Delegate to the behavior-preserving legacy runner."""
        self.runner(args)


def _build_backends() -> tuple[Backend, ...]:
    registered: list[Backend] = [
        FunctionBackend(
            name="chatgpt-codex",
            runner=run_chatgpt_codex,
            defaults=CODEX_CLI_DEFAULTS,
        ),
        FunctionBackend(
            name="claude-cli",
            runner=run_claude_cli,
            defaults=CLAUDE_CLI_DEFAULTS,
        ),
        FunctionBackend(
            name="opencode-cli",
            runner=run_opencode_cli,
            defaults=OPENCODE_DEFAULTS,
        ),
        FunctionBackend(
            name="gemini-cli",
            runner=run_gemini_cli,
            defaults=GEMINI_CLI_DEFAULTS,
        ),
    ]
    for name, runner in legacy_backends.BACKEND_RUNNERS.items():
        registered.append(
            FunctionBackend(
                name=name,
                runner=runner,
                defaults=legacy_backends.DEFAULTS[name],
            )
        )
    return tuple(registered)


def _validate_backends(registered: tuple[Backend, ...]) -> None:
    names = [backend.name for backend in registered]
    if any(not name for name in names):
        raise ValueError("Backend names must not be empty")
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"Duplicate backend names: {', '.join(duplicates)}")
    for backend in registered:
        if not callable(backend.run):
            raise TypeError(f"Backend runner is not callable: {backend.name}")
        if not isinstance(backend.defaults, Mapping):
            raise TypeError(f"Backend defaults are not a mapping: {backend.name}")


BACKENDS = _build_backends()
_validate_backends(BACKENDS)

BACKEND_BY_NAME = {backend.name: backend for backend in BACKENDS}
BACKEND_RUNNERS = {backend.name: backend.run for backend in BACKENDS}
BACKEND_DEFAULTS = {backend.name: backend.defaults for backend in BACKENDS}
