#!/usr/bin/env python3

"""Config-driven evaluation modules for the evaluator pipeline."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Mapping


class EvaluationContext(ABC):
    @property
    @abstractmethod
    def repo_root(self) -> Path:
        raise NotImplementedError

    @property
    @abstractmethod
    def case_root(self) -> Path:
        raise NotImplementedError

    @property
    @abstractmethod
    def baseline_case_root(self) -> Path | None:
        raise NotImplementedError

    @property
    @abstractmethod
    def evaluator_root(self) -> Path | None:
        raise NotImplementedError

    @property
    @abstractmethod
    def build_dir(self) -> Path | None:
        raise NotImplementedError

    @property
    @abstractmethod
    def env(self) -> Mapping[str, str]:
        raise NotImplementedError

    @property
    @abstractmethod
    def variables(self) -> Mapping[str, Any]:
        raise NotImplementedError

    def format_tokens(self) -> dict[str, str]:
        tokens = {
            "repo_root": self.repo_root.as_posix(),
            "case_root": self.case_root.as_posix(),
            "baseline_case_root": (
                self.baseline_case_root.as_posix() if self.baseline_case_root else ""
            ),
            "evaluator_root": (
                self.evaluator_root.as_posix() if self.evaluator_root else ""
            ),
            "build_dir": self.build_dir.as_posix() if self.build_dir else "",
        }
        for key, value in self.variables.items():
            tokens[key] = str(value)
        return tokens


class DefaultEvaluationContext(EvaluationContext):
    def __init__(
        self,
        *,
        repo_root: Path,
        case_root: Path,
        baseline_case_root: Path | None = None,
        evaluator_root: Path | None = None,
        build_dir: Path | None = None,
        env: Mapping[str, str] | None = None,
        variables: Mapping[str, Any] | None = None,
    ) -> None:
        self._repo_root = repo_root
        self._case_root = case_root
        self._baseline_case_root = baseline_case_root
        self._evaluator_root = evaluator_root
        self._build_dir = build_dir
        self._env = dict(env or {})
        self._variables = dict(variables or {})

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    @property
    def case_root(self) -> Path:
        return self._case_root

    @property
    def baseline_case_root(self) -> Path | None:
        return self._baseline_case_root

    @property
    def evaluator_root(self) -> Path | None:
        return self._evaluator_root

    @property
    def build_dir(self) -> Path | None:
        return self._build_dir

    @property
    def env(self) -> Mapping[str, str]:
        return self._env

    @property
    def variables(self) -> Mapping[str, Any]:
        return self._variables
