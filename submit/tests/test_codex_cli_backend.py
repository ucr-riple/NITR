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

from backends import codex_cli as backend  # noqa: E402


class CodexCliBackendTests(unittest.TestCase):
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

    def test_command_preserves_read_only_contract(self) -> None:
        command = backend.build_codex_cli_command("/project", "model", "/out")
        self.assertEqual(command[:2], ["codex", "exec"])
        self.assertEqual(command[command.index("--model") + 1], "model")
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertIn("--skip-git-repo-check", command)
        self.assertIn("--json", command)
        self.assertEqual(command[command.index("--output-last-message") + 1], "/out")

    def test_usage_extraction_supports_nested_and_missing_usage(self) -> None:
        events = "\n".join(
            [
                "not json",
                json.dumps({"type": "result", "result": {"usage": {"input": 3}}}),
            ]
        )
        self.assertEqual(
            backend.extract_codex_usage_from_events(events),
            {
                "available": True,
                "backend": "chatgpt-codex",
                "event_type": "result",
                "usage": {"input": 3},
            },
        )
        self.assertFalse(backend.extract_codex_usage_from_events("")["available"])

    @mock.patch.object(backend.time, "sleep")
    @mock.patch.object(backend.subprocess, "run")
    def test_success_applies_replacement_and_saves_usage(self, run, sleep) -> None:
        payload = {"files": [{"filename": "source.cc", "content": "after\n"}]}

        def complete(command, **_kwargs):
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text(json.dumps(payload), encoding="utf-8")
            events = json.dumps({"type": "turn.completed", "usage": {"total": 7}})
            return subprocess.CompletedProcess(command, 0, events, "")

        run.side_effect = complete
        backend.run_chatgpt_codex(self.args)

        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--model") + 1], "provider/model")
        self.assertEqual(run.call_args.kwargs["timeout"], 1800.0)
        self.assertIn("Change source", run.call_args.kwargs["input"])
        final = self.output / "cases" / self.case_slug / "source.cc"
        self.assertEqual(final.read_text(encoding="utf-8"), "after\n")
        usage = self.output / "responses" / self.case_slug / "response.usage.json"
        self.assertEqual(json.loads(usage.read_text())["usage"], {"total": 7})
        self.assertFalse(
            (
                self.output
                / "staging"
                / self.case_slug
                / "final"
                / ".codex_last_message.txt"
            ).exists()
        )
        sleep.assert_called_once_with(60.0)

    @mock.patch.object(backend.time, "sleep")
    @mock.patch.object(backend.subprocess, "run")
    def test_invalid_semantic_response_does_not_apply_files(self, run, sleep) -> None:
        def complete(command, **_kwargs):
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text("not replacement json", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        run.side_effect = complete
        with self.assertRaises(SystemExit):
            backend.run_chatgpt_codex(self.args)

        staged = self.output / "staging" / self.case_slug / "final" / "source.cc"
        self.assertEqual(staged.read_text(encoding="utf-8"), "before\n")
        self.assertFalse((self.output / "cases" / self.case_slug).exists())
        sleep.assert_not_called()

    @mock.patch.object(backend.time, "sleep")
    @mock.patch.object(backend.subprocess, "run")
    def test_terminal_failure_retries_without_applying_files(self, run, sleep) -> None:
        run.return_value = subprocess.CompletedProcess(
            ["codex"], 2, "", "provider failure"
        )

        with self.assertRaises(SystemExit):
            backend.run_chatgpt_codex(self.args)

        self.assertEqual(run.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        staged = self.output / "staging" / self.case_slug / "final" / "source.cc"
        self.assertEqual(staged.read_text(encoding="utf-8"), "before\n")
        self.assertFalse((self.output / "cases" / self.case_slug).exists())


if __name__ == "__main__":
    unittest.main()
