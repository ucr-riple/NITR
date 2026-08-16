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

import gemini_vertex_backend as backend  # noqa: E402


class GeminiVertexBackendTests(unittest.TestCase):
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
            region="us-central1",
            model_name="provider/model",
            start_step=None,
            end_step=None,
            run_label=None,
        )

    def tearDown(self) -> None:
        self.output_temp.cleanup()
        self.repo_temp.cleanup()

    def _google_modules(self, generate_effect):
        generate = mock.Mock(side_effect=generate_effect)
        client = SimpleNamespace(models=SimpleNamespace(generate_content=generate))
        client_factory = mock.Mock(return_value=client)
        config_factory = mock.Mock(return_value="generate-config")
        genai = SimpleNamespace(
            Client=client_factory,
            types=SimpleNamespace(GenerateContentConfig=config_factory),
        )
        google = SimpleNamespace(genai=genai)
        return (
            {"google": google, "google.genai": genai},
            client_factory,
            config_factory,
            generate,
        )

    @mock.patch.object(backend.time, "sleep")
    def test_success_applies_replacement_and_forwards_vertex_config(
        self, sleep
    ) -> None:
        replacement = {"files": [{"filename": "source.cc", "content": "after\n"}]}
        response = SimpleNamespace(text=json.dumps(replacement))
        modules, client_factory, config_factory, generate = self._google_modules(
            lambda **_kwargs: response
        )

        with mock.patch.dict(sys.modules, modules):
            backend.run_gemini_vertex(self.args)

        client_factory.assert_called_once_with(
            vertexai=True, project="test-project", location="us-central1"
        )
        config_factory.assert_called_once_with(
            temperature=0.7, http_options={"timeout": 1800000}
        )
        call = generate.call_args.kwargs
        self.assertEqual(call["model"], "provider/model")
        self.assertEqual(call["config"], "generate-config")
        self.assertIn("Change source", call["contents"])
        final = self.output / "cases" / self.case_slug / "source.cc"
        self.assertEqual(final.read_text(encoding="utf-8"), "after\n")
        sleep.assert_called_once_with(60.0)

    @mock.patch.object(backend.time, "sleep")
    def test_invalid_semantic_response_does_not_apply_files(self, sleep) -> None:
        modules, _client, _config, generate = self._google_modules(
            lambda **_kwargs: SimpleNamespace(text="not json")
        )
        with (
            mock.patch.dict(sys.modules, modules),
            self.assertRaises(SystemExit),
        ):
            backend.run_gemini_vertex(self.args)

        self.assertEqual(generate.call_count, 1)
        staged = self.output / "staging" / self.case_slug / "final" / "source.cc"
        self.assertEqual(staged.read_text(encoding="utf-8"), "before\n")
        self.assertFalse((self.output / "cases" / self.case_slug).exists())
        sleep.assert_not_called()

    @mock.patch.object(backend.time, "sleep")
    def test_provider_failure_retries_three_times(self, sleep) -> None:
        def fail(**_kwargs):
            raise RuntimeError("provider failure")

        modules, _client, _config, generate = self._google_modules(fail)
        with (
            mock.patch.dict(sys.modules, modules),
            self.assertRaises(SystemExit),
        ):
            backend.run_gemini_vertex(self.args)

        self.assertEqual(generate.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertFalse((self.output / "cases" / self.case_slug).exists())

    def test_missing_project_configuration_fails_before_client_creation(self) -> None:
        modules, client_factory, _config, _generate = self._google_modules(None)
        args = SimpleNamespace(**vars(self.args))
        args.project_id = None
        with (
            mock.patch.dict(sys.modules, modules),
            mock.patch.dict(backend.GEMINI_VERTEX_DEFAULTS, {"project_id": None}),
            self.assertRaisesRegex(ValueError, "--project_id"),
        ):
            backend.run_gemini_vertex(args)
        client_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
