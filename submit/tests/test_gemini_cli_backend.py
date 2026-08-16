from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

SUBMIT_DIR = Path(__file__).resolve().parents[1]
if str(SUBMIT_DIR) not in sys.path:
    sys.path.insert(0, str(SUBMIT_DIR))

from backends import gemini_cli as backend  # noqa: E402


class GeminiCliBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_temp = tempfile.TemporaryDirectory()
        self.output_temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.repo_temp.name)
        self.output = Path(self.output_temp.name)
        self.case_slug = "001.example"
        case = self.repo / "cases" / self.case_slug
        evaluator = self.repo / "evaluator" / self.case_slug
        docs = self.repo / "docs"
        case.mkdir(parents=True)
        evaluator.mkdir(parents=True)
        docs.mkdir()
        (case / "TASK.md").write_text("Change source", encoding="utf-8")
        (case / "source.cc").write_text("before\n", encoding="utf-8")
        (docs / "design_matrix.md").write_text(
            "| 001 example | dimension | micro |\n", encoding="utf-8"
        )
        self.args = SimpleNamespace(
            input_dir=str(self.repo),
            output_dir=str(self.output),
            case_id="001",
            model_name="provider/model",
            start_step=None,
            end_step=None,
            run_label=None,
        )

    def tearDown(self) -> None:
        self.output_temp.cleanup()
        self.repo_temp.cleanup()

    def test_command_includes_explicit_model(self) -> None:
        self.assertEqual(
            backend.build_gemini_cli_command("provider/model"),
            ["gemini", "--model", "provider/model"],
        )

    def test_defaults_preserve_legacy_values(self) -> None:
        self.assertEqual(
            backend.GEMINI_CLI_DEFAULTS,
            {
                "model_name": "gemini-3.1-pro-preview",
                "response_delay_seconds": 0.0,
            },
        )

    def test_prompt_preserves_json_replacement_contract(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            project = Path(root)
            (project / "TASK.md").write_text("Change source", encoding="utf-8")
            (project / "source.cc").write_text("before\n", encoding="utf-8")
            prompt = backend.build_gemini_cli_prompt(str(project), "TASK.md")
        self.assertIn('"filename": "relative/path/to/file"', prompt)
        self.assertIn('"content": "full replacement file content"', prompt)
        self.assertIn("before", prompt)
        self.assertIn("DO NOT use any tools", prompt)

    def test_prompt_rejects_project_without_source_context(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "No valid source files"):
                backend.build_gemini_cli_prompt(root, "TASK.md")

    @mock.patch.object(backend.subprocess, "run")
    def test_success_decodes_response_and_applies_replacement(self, run) -> None:
        response = {"files": [{"filename": "source.cc", "content": "after\n"}]}
        run.return_value = subprocess.CompletedProcess(
            ["gemini"], 0, json.dumps(response), ""
        )

        backend.run_gemini_cli(self.args)

        run.assert_called_once()
        call_args, call_kwargs = run.call_args
        self.assertEqual(call_args[0], ["gemini", "--model", "provider/model"])
        self.assertIn("before", call_kwargs["input"])
        self.assertTrue(call_kwargs["capture_output"])
        self.assertTrue(call_kwargs["check"])
        final = self.output / "cases" / self.case_slug / "source.cc"
        self.assertEqual(final.read_text(encoding="utf-8"), "after\n")
        artifact = self.output / "responses" / self.case_slug / "response.txt"
        self.assertEqual(json.loads(artifact.read_text()), response)

    @mock.patch.object(backend.subprocess, "run")
    def test_invalid_semantic_response_fails_without_applying_files(self, run) -> None:
        run.return_value = subprocess.CompletedProcess(
            ["gemini"], 0, "not replacement json", ""
        )

        with self.assertRaises(SystemExit):
            backend.run_gemini_cli(self.args)

        staged = self.output / "staging" / self.case_slug / "final" / "source.cc"
        self.assertEqual(staged.read_text(encoding="utf-8"), "before\n")
        self.assertFalse((self.output / "cases" / self.case_slug).exists())
        artifact = self.output / "responses" / self.case_slug / "response.txt"
        self.assertEqual(artifact.read_text(encoding="utf-8"), "not replacement json")

    @mock.patch.object(backend.subprocess, "run")
    def test_terminal_cli_failure_fails_without_response_or_replacement(
        self, run
    ) -> None:
        run.side_effect = subprocess.CalledProcessError(
            2, ["gemini"], stderr="provider failure"
        )

        with self.assertRaises(SystemExit):
            backend.run_gemini_cli(self.args)

        staged = self.output / "staging" / self.case_slug / "final" / "source.cc"
        self.assertEqual(staged.read_text(encoding="utf-8"), "before\n")
        artifact = self.output / "responses" / self.case_slug / "response.txt"
        self.assertFalse(artifact.exists())
        self.assertFalse((self.output / "cases" / self.case_slug).exists())


if __name__ == "__main__":
    unittest.main()
