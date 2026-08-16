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

import qwen_vertex_backend as backend  # noqa: E402


class QwenVertexBackendTests(unittest.TestCase):
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
            endpoint_id="endpoint-1",
            endpoint_location="us-central1",
            start_step=None,
            end_step=None,
            run_label=None,
        )

    def tearDown(self) -> None:
        self.output_temp.cleanup()
        self.repo_temp.cleanup()

    def _google_modules(self, prediction_effect):
        predict = mock.Mock(side_effect=prediction_effect)
        endpoint = SimpleNamespace(predict=predict)
        endpoint_factory = mock.Mock(return_value=endpoint)
        initialize = mock.Mock()
        aiplatform = SimpleNamespace(init=initialize, Endpoint=endpoint_factory)
        cloud = SimpleNamespace(aiplatform=aiplatform)
        google = SimpleNamespace(cloud=cloud)
        modules = {
            "google": google,
            "google.cloud": cloud,
            "google.cloud.aiplatform": aiplatform,
        }
        return modules, initialize, endpoint_factory, predict

    def test_prompt_and_chat_payloads_preserve_parameters(self) -> None:
        config = backend.QWEN_VERTEX_DEFAULTS.copy()
        instances, parameters = backend.build_qwen_vertex_payload("prompt", config)
        self.assertEqual(instances, [{"prompt": "prompt"}])
        self.assertEqual(parameters["max_tokens"], 16384)
        config["request_format"] = "chat"
        instances, parameters = backend.build_qwen_vertex_payload("prompt", config)
        self.assertIsNone(parameters)
        self.assertEqual(instances[0]["@requestFormat"], "chatCompletions")
        self.assertEqual(instances[0]["messages"][0]["content"], "prompt")

    def test_response_decoder_supports_vertex_shapes(self) -> None:
        samples = [
            ("plain", "plain"),
            ({"generated_text": "generated"}, "generated"),
            ({"choices": [{"message": {"content": "chat"}}]}, "chat"),
            ({"candidates": [{"parts": [{"text": "a"}, {"text": "b"}]}]}, "ab"),
            ({"predictions": [{"output_text": "nested"}]}, "nested"),
        ]
        for payload, expected in samples:
            with self.subTest(payload=payload):
                self.assertEqual(backend.extract_qwen_vertex_text(payload), expected)
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            backend.extract_qwen_vertex_text({"unknown": True})

    @mock.patch.object(backend.time, "sleep")
    def test_success_applies_replacement_and_forwards_endpoint_config(
        self, sleep
    ) -> None:
        replacement = {"files": [{"filename": "source.cc", "content": "after\n"}]}
        result = SimpleNamespace(predictions=[{"text": json.dumps(replacement)}])
        modules, initialize, endpoint_factory, predict = self._google_modules(
            lambda **_kwargs: result
        )

        with mock.patch.dict(sys.modules, modules):
            backend.run_qwen_vertex(self.args)

        initialize.assert_called_once_with(
            project="test-project", location="us-central1"
        )
        endpoint_factory.assert_called_once_with(
            endpoint_name="projects/test-project/locations/us-central1/endpoints/endpoint-1"
        )
        call = predict.call_args.kwargs
        self.assertIn("Change source", call["instances"][0]["prompt"])
        self.assertEqual(call["parameters"]["max_tokens"], 16384)
        self.assertEqual(call["timeout"], 1800.0)
        final = self.output / "cases" / self.case_slug / "source.cc"
        self.assertEqual(final.read_text(encoding="utf-8"), "after\n")
        sleep.assert_called_once_with(60.0)

    @mock.patch.object(backend.time, "sleep")
    def test_invalid_semantic_response_does_not_apply_files(self, sleep) -> None:
        result = SimpleNamespace(predictions=[{"text": "not json"}])
        modules, _init, _endpoint, predict = self._google_modules(
            lambda **_kwargs: result
        )
        with (
            mock.patch.dict(sys.modules, modules),
            self.assertRaises(SystemExit),
        ):
            backend.run_qwen_vertex(self.args)
        self.assertEqual(predict.call_count, 1)
        staged = self.output / "staging" / self.case_slug / "final" / "source.cc"
        self.assertEqual(staged.read_text(encoding="utf-8"), "before\n")
        self.assertFalse((self.output / "cases" / self.case_slug).exists())
        sleep.assert_not_called()

    @mock.patch.object(backend.time, "sleep")
    def test_provider_failure_retries_three_times(self, sleep) -> None:
        def fail(**_kwargs):
            raise RuntimeError("provider failure")

        modules, _init, _endpoint, predict = self._google_modules(fail)
        with (
            mock.patch.dict(sys.modules, modules),
            self.assertRaises(SystemExit),
        ):
            backend.run_qwen_vertex(self.args)
        self.assertEqual(predict.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertFalse((self.output / "cases" / self.case_slug).exists())

    def test_missing_endpoint_config_fails_before_sdk_initialization(self) -> None:
        modules, initialize, _endpoint, _predict = self._google_modules(None)
        args = SimpleNamespace(**vars(self.args))
        args.endpoint_id = None
        with (
            mock.patch.dict(sys.modules, modules),
            mock.patch.dict(backend.QWEN_VERTEX_DEFAULTS, {"endpoint_id": None}),
            self.assertRaisesRegex(ValueError, "--endpoint_id"),
        ):
            backend.run_qwen_vertex(args)
        initialize.assert_not_called()


if __name__ == "__main__":
    unittest.main()
