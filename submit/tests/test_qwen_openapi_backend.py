from __future__ import annotations

import json
import subprocess
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

from backends import qwen_openapi as backend  # noqa: E402


class QwenOpenApiBackendTests(unittest.TestCase):
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

    def _urlopen_response(self, payload):
        response = mock.MagicMock()
        response.read.return_value = json.dumps(payload).encode("utf-8")
        context = mock.MagicMock()
        context.__enter__.return_value = response
        return context

    def test_url_and_response_shape_helpers(self) -> None:
        self.assertEqual(
            backend.build_qwen_openapi_url("project", "region"),
            "https://aiplatform.googleapis.com/v1/projects/project/locations/region/"
            "endpoints/openapi/chat/completions",
        )
        self.assertEqual(
            backend.extract_qwen_openapi_text(
                {"choices": [{"message": {"content": "message"}}]}
            ),
            "message",
        )
        self.assertEqual(
            backend.extract_qwen_openapi_text({"choices": [{"text": "text"}]}),
            "text",
        )

    @mock.patch.object(backend.time, "sleep")
    @mock.patch.object(backend.urllib.request, "urlopen")
    @mock.patch.object(backend.subprocess, "run")
    def test_success_applies_replacement_and_forwards_request(
        self, run, urlopen, sleep
    ) -> None:
        run.return_value = subprocess.CompletedProcess(
            ["gcloud"], 0, "access-token\n", ""
        )
        replacement = {"files": [{"filename": "source.cc", "content": "after\n"}]}
        urlopen.return_value = self._urlopen_response(
            {"choices": [{"message": {"content": json.dumps(replacement)}}]}
        )

        backend.run_qwen_openapi(self.args)

        run.assert_called_once_with(
            ["gcloud", "auth", "print-access-token"],
            check=True,
            capture_output=True,
            text=True,
        )
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertIn("test-project/locations/us-central1", request.full_url)
        self.assertEqual(request.get_header("Authorization"), "Bearer access-token")
        self.assertEqual(payload["model"], "provider/model")
        self.assertEqual(payload["max_tokens"], 16384)
        self.assertEqual(payload["temperature"], 0.1)
        self.assertEqual(payload["top_p"], 0.95)
        self.assertIn("Change source", payload["messages"][0]["content"])
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 1800.0)
        final = self.output / "cases" / self.case_slug / "source.cc"
        self.assertEqual(final.read_text(encoding="utf-8"), "after\n")
        sleep.assert_called_once_with(60.0)

    @mock.patch.object(backend.time, "sleep")
    @mock.patch.object(backend.urllib.request, "urlopen")
    @mock.patch.object(backend.subprocess, "run")
    def test_invalid_semantic_response_does_not_apply_files(
        self, run, urlopen, sleep
    ) -> None:
        run.return_value = subprocess.CompletedProcess(["gcloud"], 0, "token", "")
        urlopen.return_value = self._urlopen_response(
            {"choices": [{"message": {"content": "not json"}}]}
        )
        with self.assertRaises(SystemExit):
            backend.run_qwen_openapi(self.args)

        staged = self.output / "staging" / self.case_slug / "final" / "source.cc"
        self.assertEqual(staged.read_text(encoding="utf-8"), "before\n")
        self.assertFalse((self.output / "cases" / self.case_slug).exists())
        sleep.assert_not_called()

    @mock.patch.object(backend.time, "sleep")
    @mock.patch.object(backend.urllib.request, "urlopen")
    @mock.patch.object(backend.subprocess, "run")
    def test_network_failure_retries_and_refreshes_token(
        self, run, urlopen, sleep
    ) -> None:
        run.return_value = subprocess.CompletedProcess(["gcloud"], 0, "token", "")
        urlopen.side_effect = urllib.error.URLError("offline")
        with self.assertRaises(SystemExit):
            backend.run_qwen_openapi(self.args)

        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(run.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertFalse((self.output / "cases" / self.case_slug).exists())

    @mock.patch.object(backend.subprocess, "run")
    def test_empty_access_token_is_rejected(self, run) -> None:
        run.return_value = subprocess.CompletedProcess(["gcloud"], 0, "  ", "")
        with self.assertRaisesRegex(ValueError, "empty access token"):
            backend.get_gcloud_access_token()

    @mock.patch.object(backend.subprocess, "run")
    def test_missing_project_fails_before_token_request(self, run) -> None:
        args = SimpleNamespace(**vars(self.args))
        args.project_id = None
        with (
            mock.patch.dict(backend.QWEN_OPENAPI_DEFAULTS, {"project_id": None}),
            self.assertRaisesRegex(ValueError, "--project_id"),
        ):
            backend.run_qwen_openapi(args)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
