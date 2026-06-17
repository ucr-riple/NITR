#!/usr/bin/env python3

"""Shared test helpers for evaluator module unit tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evaluator.shared.context import DefaultEvaluationContext


class ModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name).resolve()
        self.case_root = (self.repo_root / "case").resolve()
        self.baseline_root = (self.repo_root / "baseline").resolve()
        self.build_dir = (self.repo_root / "build").resolve()
        self.bin_dir = (self.repo_root / "bin").resolve()
        self.case_root.mkdir(parents=True, exist_ok=True)
        self.baseline_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _context(
        self,
        *,
        env: dict[str, str] | None = None,
    ) -> DefaultEvaluationContext:
        return DefaultEvaluationContext(
            repo_root=self.repo_root,
            case_root=self.case_root,
            baseline_case_root=self.baseline_root,
            evaluator_root=self.repo_root / "evaluator_case",
            build_dir=self.build_dir,
            env=env or {},
        )

    def _write(self, root: Path, relative_path: str, content: str = "") -> None:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _mkdir(self, root: Path, relative_path: str) -> None:
        (root / relative_path).mkdir(parents=True, exist_ok=True)

    def _write_executable(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)


class ProcessModuleTestCase(ModuleTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.bin_dir.mkdir(parents=True, exist_ok=True)
