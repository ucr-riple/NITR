#!/usr/bin/env python3

"""Local integration tests for pipeline evaluation against materialized outputs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

PIPELINE_TIMEOUT_SECONDS = 300


class SubmissionPipelineIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[4]
        fixture_root = os.environ.get("NITR_SUBMIT_OUTPUT_ROOT")
        if fixture_root:
            cls.fixture_root = Path(fixture_root).resolve()
        else:
            cls.fixture_root = (
                cls.repo_root
                / "evaluator"
                / "shared"
                / "module"
                / "testdata"
                / "submission_pipeline"
            ).resolve()
        if not cls.fixture_root.is_dir():
            raise unittest.SkipTest(
                f"submission pipeline fixture root not found: {cls.fixture_root}"
            )
        manifest_path = cls.fixture_root / "manifest.json"
        if not manifest_path.is_file():
            raise unittest.SkipTest(
                f"submission pipeline manifest not found: {manifest_path}"
            )
        cls.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        samples = cls.manifest.get("samples")
        if not isinstance(samples, list):
            raise ValueError(
                "submission pipeline manifest must contain a 'samples' list"
            )
        for index, sample in enumerate(samples):
            if not isinstance(sample, dict):
                raise ValueError(
                    f"invalid manifest sample at index {index}: expected object, "
                    f"got {type(sample).__name__}"
                )
            missing_keys = [
                key for key in ("backend", "case_slug") if key not in sample
            ]
            if missing_keys:
                raise ValueError(
                    f"invalid manifest sample at index {index}: missing "
                    f"{', '.join(repr(key) for key in missing_keys)} in {sample}"
                )

    def _run_pipeline(self, backend: str, case_slug: str) -> dict[str, object]:
        generated_case_root = self.fixture_root / backend / "cases" / case_slug
        if not generated_case_root.is_dir():
            self.fail(f"missing generated case fixture: {generated_case_root}")

        pipeline_config = self.repo_root / "evaluator" / case_slug / "pipeline.json"
        if not pipeline_config.is_file():
            self.fail(f"missing pipeline config: {pipeline_config}")
        command = [
            sys.executable,
            str(self.repo_root / "evaluator" / "run_evaluation_pipeline.py"),
            str(pipeline_config),
            "--override",
            f"case_root={generated_case_root}",
        ]
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=PIPELINE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(
                f"pipeline timed out after {PIPELINE_TIMEOUT_SECONDS}s for "
                f"{backend}/{case_slug}\n"
                f"stdout:\n{exc.stdout or ''}\n"
                f"stderr:\n{exc.stderr or ''}"
            )
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                f"pipeline failed for {backend}/{case_slug}\n"
                f"command: {' '.join(command)}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            ),
        )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self.fail(
                f"pipeline output was not valid JSON for {backend}/{case_slug}: {exc}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        return payload

    def test_materialized_submit_outputs_pass_pipeline(self) -> None:
        samples = self.manifest["samples"]
        self.assertGreater(len(samples), 0, "submission pipeline manifest is empty")
        for sample in samples:
            backend = sample["backend"]
            case_slug = sample["case_slug"]
            with self.subTest(
                backend=backend,
                case_slug=case_slug,
                description=sample.get("description"),
            ):
                payload = self._run_pipeline(backend, case_slug)
                self.assertTrue(payload["passed"])
                self.assertGreaterEqual(payload["summary"]["total_modules"], 1)
                self.assertEqual(payload["summary"]["failed_modules"], 0)
                self.assertIsNotNone(payload["workspace_root"])
                self.assertTrue(
                    Path(payload["case_root"]).resolve().as_posix().endswith(case_slug)
                )


if __name__ == "__main__":
    unittest.main()
