from __future__ import annotations

import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

SUBMIT_DIR = Path(__file__).resolve().parents[1]
if str(SUBMIT_DIR) not in sys.path:
    sys.path.insert(0, str(SUBMIT_DIR))

import chatgpt_api_backend as backend  # noqa: E402


class ChatGptApiBackendTests(unittest.TestCase):
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

    def _urlopen_response(self, payload):
        response = mock.MagicMock()
        response.read.return_value = json.dumps(payload).encode("utf-8")
        context = mock.MagicMock()
        context.__enter__.return_value = response
        return context

    def test_extracts_top_level_and_nested_response_text(self) -> None:
        self.assertEqual(
            backend.extract_openai_response_text({"output_text": "direct"}),
            "direct",
        )
        nested = {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "nested"}],
                }
            ]
        }
        self.assertEqual(backend.extract_openai_response_text(nested), "nested")

    @mock.patch.object(backend.time, "sleep")
    @mock.patch.object(backend.urllib.request, "urlopen")
    def test_success_applies_replacement_and_saves_api_artifacts(
        self, urlopen, sleep
    ) -> None:
        replacement = {"files": [{"filename": "source.cc", "content": "after\n"}]}
        api_payload = {
            "output_text": json.dumps(replacement),
            "usage": {"input_tokens": 5},
        }
        urlopen.return_value = self._urlopen_response(api_payload)

        with mock.patch.dict(backend.os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend.run_chatgpt_api(self.args)

        request = urlopen.call_args.args[0]
        request_payload = json.loads(request.data)
        self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(request_payload["model"], "provider/model")
        self.assertEqual(request_payload["max_output_tokens"], 32768)
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 1800.0)
        final = self.output / "cases" / self.case_slug / "source.cc"
        self.assertEqual(final.read_text(encoding="utf-8"), "after\n")
        response_dir = self.output / "responses" / self.case_slug
        self.assertEqual(
            json.loads((response_dir / "response.api_response.json").read_text()),
            api_payload,
        )
        self.assertEqual(
            json.loads((response_dir / "response.usage.json").read_text()),
            {"input_tokens": 5},
        )
        sleep.assert_called_once_with(15.0)

    @mock.patch.object(backend.time, "sleep")
    @mock.patch.object(backend.urllib.request, "urlopen")
    def test_invalid_semantic_response_saves_artifacts_without_applying(
        self, urlopen, sleep
    ) -> None:
        api_payload = {"output_text": "not replacement json", "usage": {}}
        urlopen.return_value = self._urlopen_response(api_payload)

        with (
            mock.patch.dict(backend.os.environ, {"OPENAI_API_KEY": "test-key"}),
            self.assertRaises(SystemExit),
        ):
            backend.run_chatgpt_api(self.args)

        staged = self.output / "staging" / self.case_slug / "final" / "source.cc"
        self.assertEqual(staged.read_text(encoding="utf-8"), "before\n")
        self.assertFalse((self.output / "cases" / self.case_slug).exists())
        response_dir = self.output / "responses" / self.case_slug
        self.assertTrue((response_dir / "response.api_response.json").exists())
        self.assertTrue((response_dir / "response.usage.json").exists())
        sleep.assert_not_called()

    @mock.patch.object(backend.time, "sleep")
    @mock.patch.object(backend.urllib.request, "urlopen")
    def test_network_failure_retries_and_does_not_apply(self, urlopen, sleep) -> None:
        urlopen.side_effect = urllib.error.URLError("offline")
        with (
            mock.patch.dict(backend.os.environ, {"OPENAI_API_KEY": "test-key"}),
            self.assertRaises(SystemExit),
        ):
            backend.run_chatgpt_api(self.args)

        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertFalse((self.output / "cases" / self.case_slug).exists())

    @mock.patch.object(backend.urllib.request, "urlopen")
    def test_missing_api_key_fails_before_network_request(self, urlopen) -> None:
        with (
            mock.patch.dict(backend.os.environ, {}, clear=True),
            self.assertRaises(SystemExit),
        ):
            backend.run_chatgpt_api(self.args)
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
