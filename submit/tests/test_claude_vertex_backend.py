from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

SUBMIT_DIR = Path(__file__).resolve().parents[1]
if str(SUBMIT_DIR) not in sys.path:
    sys.path.insert(0, str(SUBMIT_DIR))

from backends import claude_vertex as backend  # noqa: E402


class ClaudeVertexBackendTests(unittest.TestCase):
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
            project_id="test-project",
            region="us-east5",
            model_name="provider/model",
            start_step=None,
            end_step=None,
            run_label=None,
        )

    def tearDown(self) -> None:
        self.output_temp.cleanup()
        self.repo_temp.cleanup()

    def _anthropic_module(self, create_effect):
        create = mock.Mock(side_effect=create_effect)
        client = SimpleNamespace(messages=SimpleNamespace(create=create))
        factory = mock.Mock(return_value=client)
        module = SimpleNamespace(AnthropicVertex=factory)
        return module, factory, create

    def test_message_text_flattens_blocks_and_rejects_empty_content(self) -> None:
        message = SimpleNamespace(
            content=[SimpleNamespace(text="first"), SimpleNamespace(text="second")]
        )
        self.assertEqual(backend.extract_claude_message_text(message), "firstsecond")
        with self.assertRaisesRegex(ValueError, "text blocks"):
            backend.extract_claude_message_text(SimpleNamespace(content=[]))

    @mock.patch.object(backend.time, "sleep")
    def test_success_applies_replacement_and_forwards_vertex_config(
        self, sleep
    ) -> None:
        replacement = {"files": [{"filename": "source.cc", "content": "after\n"}]}
        message = SimpleNamespace(
            content=[SimpleNamespace(text=json.dumps(replacement))]
        )
        module, factory, create = self._anthropic_module(lambda **_kwargs: message)

        with mock.patch.dict(sys.modules, {"anthropic": module}):
            backend.run_claude_vertex(self.args)

        factory.assert_called_once_with(region="us-east5", project_id="test-project")
        call = create.call_args.kwargs
        self.assertEqual(call["model"], "provider/model")
        self.assertEqual(call["max_tokens"], 32768)
        self.assertEqual(call["timeout"], 1800.0)
        self.assertEqual(call["messages"][0]["role"], "user")
        self.assertIn("Change source", call["messages"][0]["content"])
        final = self.output / "cases" / self.case_slug / "source.cc"
        self.assertEqual(final.read_text(encoding="utf-8"), "after\n")
        sleep.assert_called_once_with(60.0)

    @mock.patch.object(backend.time, "sleep")
    def test_invalid_semantic_response_does_not_apply_files(self, sleep) -> None:
        message = SimpleNamespace(content=[SimpleNamespace(text="not json")])
        module, _factory, create = self._anthropic_module(lambda **_kwargs: message)

        with (
            mock.patch.dict(sys.modules, {"anthropic": module}),
            self.assertRaises(SystemExit),
        ):
            backend.run_claude_vertex(self.args)

        self.assertEqual(create.call_count, 1)
        staged = self.output / "staging" / self.case_slug / "final" / "source.cc"
        self.assertEqual(staged.read_text(encoding="utf-8"), "before\n")
        self.assertFalse((self.output / "cases" / self.case_slug).exists())
        sleep.assert_not_called()

    @mock.patch.object(backend.time, "sleep")
    def test_provider_failure_retries_three_times(self, sleep) -> None:
        module, _factory, create = self._anthropic_module(
            lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("provider failure"))
        )
        with (
            mock.patch.dict(sys.modules, {"anthropic": module}),
            self.assertRaises(SystemExit),
        ):
            backend.run_claude_vertex(self.args)

        self.assertEqual(create.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertFalse((self.output / "cases" / self.case_slug).exists())

    def test_missing_project_configuration_fails_before_client_creation(self) -> None:
        module, factory, _create = self._anthropic_module(None)
        args = SimpleNamespace(**vars(self.args))
        args.project_id = None
        with (
            mock.patch.dict(sys.modules, {"anthropic": module}),
            mock.patch.dict(backend.CLAUDE_VERTEX_DEFAULTS, {"project_id": None}),
            self.assertRaisesRegex(ValueError, "--project_id"),
        ):
            backend.run_claude_vertex(args)
        factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
