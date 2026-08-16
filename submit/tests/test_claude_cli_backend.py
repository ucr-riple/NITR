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

from backends import claude_cli as backend  # noqa: E402


class ClaudeCliBackendTests(unittest.TestCase):
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

    def test_command_and_prompt_preserve_contract(self) -> None:
        prompt = backend.build_claude_cli_prompt("TASK.md")
        command = backend.build_claude_cli_command(prompt, "model", "Read")
        self.assertEqual(command[:2], ["claude", "-p"])
        self.assertEqual(command[command.index("--model") + 1], "model")
        self.assertEqual(command[command.index("--allowedTools") + 1], "Read")
        self.assertIn('"filename": "relative/path/to/file"', prompt)
        self.assertIn("modified AND newly created", prompt)

    @mock.patch.object(backend.time, "sleep")
    @mock.patch.object(backend.subprocess, "run")
    def test_success_saves_transcript_and_applies_replacement(self, run, sleep) -> None:
        payload = {"files": [{"filename": "source.cc", "content": "after\n"}]}
        run.return_value = subprocess.CompletedProcess(
            ["claude"], 0, json.dumps(payload), "diagnostic"
        )

        backend.run_claude_cli(self.args)

        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--model") + 1], "provider/model")
        self.assertEqual(run.call_args.kwargs["timeout"], 1800.0)
        final = self.output / "cases" / self.case_slug / "source.cc"
        self.assertEqual(final.read_text(encoding="utf-8"), "after\n")
        response = self.output / "responses" / self.case_slug / "response.txt"
        transcript = response.with_name("response.transcript.txt")
        self.assertEqual(json.loads(response.read_text()), payload)
        self.assertIn("=== STDERR ===\ndiagnostic", transcript.read_text())
        sleep.assert_called_once_with(10.0)

    @mock.patch.object(backend.time, "sleep")
    @mock.patch.object(backend.subprocess, "run")
    def test_invalid_semantic_response_does_not_apply_files(self, run, sleep) -> None:
        run.return_value = subprocess.CompletedProcess(
            ["claude"], 0, "not replacement json", ""
        )

        with self.assertRaises(SystemExit):
            backend.run_claude_cli(self.args)

        staged = self.output / "staging" / self.case_slug / "final" / "source.cc"
        self.assertEqual(staged.read_text(encoding="utf-8"), "before\n")
        self.assertFalse((self.output / "cases" / self.case_slug).exists())
        sleep.assert_not_called()

    @mock.patch.object(backend.time, "sleep")
    @mock.patch.object(backend.subprocess, "run")
    def test_terminal_failure_retries_and_does_not_apply_files(
        self, run, sleep
    ) -> None:
        run.return_value = subprocess.CompletedProcess(
            ["claude"], 2, "", "provider failure"
        )

        with self.assertRaises(SystemExit):
            backend.run_claude_cli(self.args)

        self.assertEqual(run.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        staged = self.output / "staging" / self.case_slug / "final" / "source.cc"
        self.assertEqual(staged.read_text(encoding="utf-8"), "before\n")
        self.assertFalse((self.output / "cases" / self.case_slug).exists())
        transcript = (
            self.output / "responses" / self.case_slug / "response.transcript.txt"
        )
        self.assertIn("provider failure", transcript.read_text())

    @mock.patch.object(backend.subprocess, "run", side_effect=FileNotFoundError)
    def test_missing_cli_has_actionable_error(self, _run) -> None:
        config = backend.CLAUDE_CLI_DEFAULTS.copy()
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(RuntimeError, "npm install"):
                backend.call_claude_cli("prompt", root, f"{root}/response.txt", config)


if __name__ == "__main__":
    unittest.main()
