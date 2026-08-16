from __future__ import annotations

import json
import os
import shutil
import stat
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

import backends  # noqa: E402
import opencode_backend as backend  # noqa: E402


def event(event_type: str, session_id: str = "session-1", **values: object) -> str:
    return json.dumps({"type": event_type, "sessionID": session_id, **values})


def final_stream(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            event("step_start", part={}),
            event(
                "text",
                part={"messageID": "message-1", "text": json.dumps(payload)},
            ),
            event("step_finish", part={}),
        ]
    )


class OpenCodeDecoderTests(unittest.TestCase):
    def test_extracts_only_final_message_and_ignores_tool_json(self) -> None:
        stream = "\n".join(
            [
                event(
                    "text",
                    part={"messageID": "early", "text": "I will inspect first."},
                ),
                event("tool_use", part={"output": {"looks": "like JSON"}}),
                event(
                    "text",
                    part={"messageID": "final", "text": '{"files": ['},
                ),
                event(
                    "text",
                    part={"messageID": "final", "text": "]}"},
                ),
            ]
        )
        self.assertEqual(backend.extract_opencode_final_text(stream), '{"files": []}')

    def test_rejects_malformed_lines(self) -> None:
        with self.assertRaisesRegex(backend.OpenCodeContractError, "Malformed"):
            backend.extract_opencode_final_text("not json")

    def test_ignores_child_session_events(self) -> None:
        stream = "\n".join(
            [
                event(
                    "text",
                    "session-1",
                    part={"messageID": "root", "text": '{"files": []}'},
                ),
                event(
                    "text",
                    "session-2",
                    part={"messageID": "child", "text": "child response"},
                ),
                event("tool_use", "session-2", part={"output": "ignored"}),
            ]
        )
        self.assertEqual(backend.extract_opencode_final_text(stream), '{"files": []}')

    def test_rejects_error_and_malformed_text_events(self) -> None:
        with self.assertRaisesRegex(backend.OpenCodeContractError, "reported an error"):
            backend.extract_opencode_final_text(event("error", error={"name": "bad"}))
        with self.assertRaisesRegex(backend.OpenCodeContractError, "messageID"):
            backend.extract_opencode_final_text(
                event("text", part={"text": "missing id"})
            )


class OpenCodeIsolationTests(unittest.TestCase):
    def test_backend_is_registered(self) -> None:
        self.assertIs(
            backends.BACKEND_RUNNERS["opencode-cli"], backend.run_opencode_cli
        )

    def test_command_model_override_is_optional(self) -> None:
        command = backend.build_opencode_command("/tmp/project", "prompt", None)
        self.assertNotIn("--model", command)
        command = backend.build_opencode_command(
            "/tmp/project", "prompt", "provider/model"
        )
        self.assertEqual(command[command.index("--model") + 1], "provider/model")
        self.assertIn("--format", command)
        self.assertIn("--pure", command)

    def test_environment_overrides_hostile_parent_config(self) -> None:
        hostile = {
            "OPENCODE_CONFIG": "/hostile/config",
            "OPENCODE_CONFIG_CONTENT": '{"permission":"allow"}',
            "OPENCODE_CONFIG_DIR": "/hostile/dir",
            "OPENCODE_PERMISSION": '{"*":"allow"}',
        }
        with (
            tempfile.TemporaryDirectory() as temp_root,
            mock.patch.dict(os.environ, hostile, clear=False),
            mock.patch.object(backend, "_copy_auth_file"),
        ):
            environment = backend.build_opencode_environment(temp_root)
        config = json.loads(environment["OPENCODE_CONFIG_CONTENT"])
        permission = json.loads(environment["OPENCODE_PERMISSION"])
        self.assertEqual(permission, backend.OPENCODE_PERMISSION)
        self.assertEqual(config["permission"], backend.OPENCODE_PERMISSION)
        self.assertEqual(
            config["agent"]["build"]["permission"], backend.OPENCODE_PERMISSION
        )
        self.assertNotEqual(environment["OPENCODE_CONFIG_DIR"], "/hostile/dir")
        self.assertEqual(environment["OPENCODE_DISABLE_PROJECT_CONFIG"], "1")

    def test_preflight_rejects_config_and_instruction_surfaces(self) -> None:
        for name in backend.FORBIDDEN_PROJECT_NAMES:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as project:
                path = Path(project, "nested", name)
                if name == ".opencode":
                    path.mkdir(parents=True)
                else:
                    path.parent.mkdir(parents=True)
                    path.write_text("hostile", encoding="utf-8")
                with self.assertRaises(backend.OpenCodeContractError):
                    backend.validate_opencode_case_preflight(project)

    def test_snapshot_detects_files_directories_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as project:
            root = Path(project)
            (root / "src").mkdir()
            (root / "src" / "file.txt").write_text("before", encoding="utf-8")
            os.symlink("src/file.txt", root / "link")
            before = backend.snapshot_project_tree(project)
            (root / "src" / "file.txt").write_text("after", encoding="utf-8")
            (root / "empty").mkdir()
            (root / "link").unlink()
            os.symlink("missing", root / "link")
            changed = backend.changed_snapshot_paths(
                before, backend.snapshot_project_tree(project)
            )
            self.assertEqual(changed, ["empty", "link", "src/file.txt"])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO is not supported")
    def test_snapshot_rejects_special_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as project:
            os.mkfifo(Path(project, "pipe"), stat.S_IRUSR | stat.S_IWUSR)
            with self.assertRaises(backend.OpenCodeContractError):
                backend.snapshot_project_tree(project)

    @unittest.skipUnless(shutil.which("git"), "git is not installed")
    def test_real_git_boundary_is_independent_of_parent_repository(self) -> None:
        with (
            tempfile.TemporaryDirectory(prefix="nitr-ancestor-") as ancestor,
            tempfile.TemporaryDirectory(prefix="nitr-opencode-boundary-") as temp_root,
        ):
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=ancestor,
                check=True,
                capture_output=True,
                text=True,
            )
            Path(ancestor, "AGENTS.md").write_text(
                "ancestor instruction", encoding="utf-8"
            )
            Path(ancestor, ".opencode").mkdir()

            project = Path(temp_root, "project")
            project.mkdir()
            (project / "TASK.md").write_text("task", encoding="utf-8")
            backend.initialize_git_boundary(str(project), temp_root)

            top_level = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(os.path.realpath(top_level), os.path.realpath(project))
            self.assertFalse(project.is_relative_to(Path(ancestor)))
            self.assertTrue((project / ".git").is_dir())
            self.assertFalse((project / "AGENTS.md").exists())
            self.assertFalse((project / ".opencode").exists())


class OpenCodeProcessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project_temp = tempfile.TemporaryDirectory()
        self.project = Path(self.project_temp.name)
        (self.project / "TASK.md").write_text("Task", encoding="utf-8")
        (self.project / "source.txt").write_text("before", encoding="utf-8")
        self.response = str(self.project / "artifacts" / "response.txt")
        self.config = {
            "cli_timeout_seconds": 5,
            "request_retry_attempts": 3,
            "request_retry_delay_seconds": 0,
        }

    def tearDown(self) -> None:
        self.project_temp.cleanup()

    def _run_side_effect(self, opencode_effect):
        def run(command, **kwargs):
            if command[:2] == ["git", "init"]:
                Path(kwargs["cwd"], ".git").mkdir()
                return subprocess.CompletedProcess(command, 0, "", "")
            return opencode_effect(command, **kwargs)

        return run

    @mock.patch.object(backend, "_copy_auth_file")
    def test_success_uses_isolated_workspace(self, _copy_auth) -> None:
        seen: dict[str, object] = {}

        def opencode(command, **kwargs):
            seen["command"] = command
            seen["cwd"] = kwargs["cwd"]
            seen["env"] = kwargs["env"]
            self.assertNotEqual(os.path.realpath(kwargs["cwd"]), str(self.project))
            self.assertEqual(command[command.index("--dir") + 1], kwargs["cwd"])
            return subprocess.CompletedProcess(
                command,
                0,
                final_stream(
                    {"files": [{"filename": "source.txt", "content": "after"}]}
                ),
                "",
            )

        with mock.patch.object(
            backend.subprocess,
            "run",
            side_effect=self._run_side_effect(opencode),
        ):
            text = backend.call_opencode(
                persistent_input=str(self.project),
                prompt=backend.build_opencode_prompt("TASK.md"),
                model_name="provider/model",
                response_output_path=self.response,
                config=self.config,
            )
        self.assertEqual(json.loads(text)["files"][0]["content"], "after")
        self.assertTrue(Path(backend.transcript_output_path(self.response)).is_file())
        self.assertFalse(Path(str(seen["cwd"])).exists())

    @mock.patch.object(backend, "_copy_auth_file")
    def test_workspace_mutation_is_not_retried(self, _copy_auth) -> None:
        invocation_count = 0

        def opencode(command, **kwargs):
            nonlocal invocation_count
            invocation_count += 1
            Path(kwargs["cwd"], "source.txt").write_text("mutated", encoding="utf-8")
            return subprocess.CompletedProcess(
                command,
                0,
                final_stream(
                    {"files": [{"filename": "source.txt", "content": "after"}]}
                ),
                "",
            )

        with (
            mock.patch.object(
                backend.subprocess,
                "run",
                side_effect=self._run_side_effect(opencode),
            ),
            self.assertRaisesRegex(backend.OpenCodeContractError, "modified"),
        ):
            backend.call_opencode(
                persistent_input=str(self.project),
                prompt="prompt",
                model_name=None,
                response_output_path=self.response,
                config=self.config,
            )
        self.assertEqual(invocation_count, 1)

    @mock.patch.object(backend, "_copy_auth_file")
    def test_explicit_transient_failure_retries_in_fresh_workspace(
        self, _copy_auth
    ) -> None:
        workspaces: list[str] = []

        def opencode(command, **kwargs):
            workspaces.append(kwargs["cwd"])
            if len(workspaces) == 1:
                return subprocess.CompletedProcess(
                    command, 1, "", "429 service unavailable"
                )
            return subprocess.CompletedProcess(
                command, 0, final_stream({"files": []}), ""
            )

        with mock.patch.object(
            backend.subprocess,
            "run",
            side_effect=self._run_side_effect(opencode),
        ):
            backend.call_opencode(
                persistent_input=str(self.project),
                prompt="prompt",
                model_name=None,
                response_output_path=self.response,
                config=self.config,
            )
        self.assertEqual(len(workspaces), 2)
        self.assertNotEqual(workspaces[0], workspaces[1])

    @mock.patch.object(backend, "_copy_auth_file")
    def test_malformed_output_and_timeout_are_not_retried(self, _copy_auth) -> None:
        for outcome in ("not-json", subprocess.TimeoutExpired("opencode", 1)):
            with self.subTest(outcome=type(outcome).__name__):
                invocation_count = 0

                def opencode(command, **kwargs):
                    nonlocal invocation_count
                    invocation_count += 1
                    if isinstance(outcome, BaseException):
                        raise outcome
                    return subprocess.CompletedProcess(command, 0, outcome, "")

                with (
                    mock.patch.object(
                        backend.subprocess,
                        "run",
                        side_effect=self._run_side_effect(opencode),
                    ),
                    self.assertRaises(backend.OpenCodeError),
                ):
                    backend.call_opencode(
                        persistent_input=str(self.project),
                        prompt="prompt",
                        model_name=None,
                        response_output_path=self.response,
                        config=self.config,
                    )
                self.assertEqual(invocation_count, 1)


class OpenCodeIntegrationTests(unittest.TestCase):
    def test_multistep_uses_nitr_applied_persistent_state(self) -> None:
        with (
            tempfile.TemporaryDirectory() as repo,
            tempfile.TemporaryDirectory() as output,
        ):
            repo_root = Path(repo)
            case = repo_root / "cases" / "001.example"
            evaluator = repo_root / "evaluator" / "001.example"
            docs = repo_root / "docs"
            case.mkdir(parents=True)
            evaluator.mkdir(parents=True)
            docs.mkdir()
            (case / "TASK1.md").write_text("first", encoding="utf-8")
            (case / "TASK2.md").write_text("second", encoding="utf-8")
            (case / "source.txt").write_text("initial", encoding="utf-8")
            (docs / "design_matrix.md").write_text(
                "| 001 example | dimension | multi-step |\n", encoding="utf-8"
            )
            seen_sources: list[str] = []

            def fake_call_opencode(**kwargs):
                source = Path(kwargs["persistent_input"], "source.txt").read_text(
                    encoding="utf-8"
                )
                seen_sources.append(source)
                replacement = "step-one" if len(seen_sources) == 1 else "step-two"
                return json.dumps(
                    {"files": [{"filename": "source.txt", "content": replacement}]}
                )

            args = SimpleNamespace(
                input_dir=repo,
                output_dir=output,
                case_id="001",
                model_name=None,
                start_step=None,
                end_step=None,
                run_label=None,
            )
            with mock.patch.object(
                backend, "call_opencode", side_effect=fake_call_opencode
            ):
                backend.run_opencode_cli(args)

            self.assertEqual(seen_sources, ["initial", "step-one"])
            final = Path(output, "cases", "001.example", "source.txt")
            self.assertEqual(final.read_text(encoding="utf-8"), "step-two")


if __name__ == "__main__":
    unittest.main()
