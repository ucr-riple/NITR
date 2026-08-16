from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

SUBMIT_DIR = Path(__file__).resolve().parents[1]
if str(SUBMIT_DIR) not in sys.path:
    sys.path.insert(0, str(SUBMIT_DIR))

import backend_registry as registry  # noqa: E402
import backends as legacy_backends  # noqa: E402
import submit_case  # noqa: E402
from backend_interface import Backend  # noqa: E402


class BackendRegistryTests(unittest.TestCase):
    def test_registry_preserves_backend_names_and_defaults(self) -> None:
        expected_names = set(legacy_backends.BACKEND_RUNNERS) | {
            "gemini-cli",
            "opencode-cli",
        }
        self.assertEqual(set(registry.BACKEND_BY_NAME), expected_names)
        self.assertEqual(set(registry.BACKEND_DEFAULTS), expected_names)
        for name, defaults in legacy_backends.DEFAULTS.items():
            self.assertEqual(dict(registry.BACKEND_DEFAULTS[name]), defaults)

    def test_every_registered_backend_implements_interface(self) -> None:
        self.assertTrue(registry.BACKENDS)
        self.assertEqual(
            len({backend.name for backend in registry.BACKENDS}),
            len(registry.BACKENDS),
        )
        for backend in registry.BACKENDS:
            self.assertIsInstance(backend, Backend)
            self.assertTrue(callable(backend.run))

    def test_registry_defaults_are_immutable_copies(self) -> None:
        registered = registry.BACKEND_DEFAULTS["chatgpt-api"]
        with self.assertRaises(TypeError):
            registered["model_name"] = "changed"  # type: ignore[index]
        self.assertIsNot(registered, legacy_backends.DEFAULTS["chatgpt-api"])

    def test_opencode_uses_function_adapter(self) -> None:
        backend = registry.BACKEND_BY_NAME["opencode-cli"]
        self.assertIsInstance(backend, registry.FunctionBackend)

    def test_gemini_cli_is_owned_by_registry_module(self) -> None:
        backend = registry.BACKEND_BY_NAME["gemini-cli"]
        self.assertIsInstance(backend, registry.FunctionBackend)
        self.assertEqual(
            dict(backend.defaults),
            {
                "model_name": "gemini-3.1-pro-preview",
                "response_delay_seconds": 0.0,
            },
        )

    def test_legacy_backends_use_behavior_preserving_adapters(self) -> None:
        for name, runner in legacy_backends.BACKEND_RUNNERS.items():
            backend = registry.BACKEND_BY_NAME[name]
            self.assertIsInstance(backend, registry.FunctionBackend)
            self.assertIs(backend.runner, runner)

    def test_parser_choices_come_from_registry(self) -> None:
        parser = submit_case.build_parser()
        backend_action = next(
            action for action in parser._actions if action.dest == "backend"
        )
        self.assertEqual(set(backend_action.choices), set(registry.BACKEND_BY_NAME))

    def test_registry_runner_is_cli_compatible(self) -> None:
        for runner in registry.BACKEND_RUNNERS.values():
            self.assertTrue(callable(runner))
        self.assertIsInstance(argparse.Namespace(), argparse.Namespace)

    def test_function_backends_use_identity_hashing(self) -> None:
        backend = registry.BACKEND_BY_NAME["opencode-cli"]
        self.assertEqual(hash(backend), object.__hash__(backend))


if __name__ == "__main__":
    unittest.main()
