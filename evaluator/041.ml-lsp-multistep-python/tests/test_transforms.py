#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
import sys
import unittest
from collections.abc import Sequence
from pathlib import Path

ARG_PARSER = argparse.ArgumentParser()
ARG_PARSER.add_argument("--case_root", required=True)
ARGS = ARG_PARSER.parse_args()

CASE_ROOT = Path(ARGS.case_root).resolve()
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))

from src.clamp_transform import ClampTransform
from src.feature_pipeline import FeaturePipeline
from src.feature_transform import FeatureTransform
from src.identity_transform import IdentityTransform
from src.l2_normalize_transform import L2NormalizeTransform
from src.transform_batch import transform_batch
from src.transform_chain import TransformChain
from src.transform_factory import make_transform


class OffsetTransform(FeatureTransform):
    def __init__(self, offset: float) -> None:
        self._offset = offset

    def transform(self, input_values: Sequence[float]) -> list[float]:
        return [value + self._offset for value in input_values]


class TransformTests(unittest.TestCase):
    def assert_vector_close(
        self, actual: Sequence[float], expected: Sequence[float]
    ) -> None:
        self.assertEqual(len(actual), len(expected))
        for actual_value, expected_value in zip(actual, expected):
            self.assertAlmostEqual(actual_value, expected_value, places=6)

    def assert_shared_contract(self, transform: FeatureTransform) -> None:
        values = [2.0, -4.0, 0.5]
        snapshot = values.copy()
        output = FeaturePipeline(transform).run(values)
        self.assertEqual(values, snapshot)
        self.assertEqual(len(output), len(values))
        self.assertTrue(all(math.isfinite(value) for value in output))
        self.assertEqual(transform.transform([]), [])

    def test_all_builtin_transforms_share_contract(self) -> None:
        for name in ("identity", "l2", "clamp"):
            with self.subTest(name=name):
                self.assert_shared_contract(make_transform(name))

    def test_clamp_limits_values(self) -> None:
        values = [-2.0, -1.0, -0.25, 0.25, 1.0, 2.0]
        snapshot = values.copy()
        self.assertEqual(
            ClampTransform().transform(values),
            [-1.0, -1.0, -0.25, 0.25, 1.0, 1.0],
        )
        self.assertEqual(values, snapshot)

    def test_l2_zero_and_nonzero_contract(self) -> None:
        self.assertEqual(L2NormalizeTransform().transform([0.0, 0.0]), [0.0, 0.0])
        output = L2NormalizeTransform().transform([1.0, 2.0, 2.0])
        self.assertAlmostEqual(math.sqrt(sum(value * value for value in output)), 1.0)

    def test_batch_uses_any_feature_transform(self) -> None:
        batch = [[1.0, 2.0], [], [-3.0]]
        snapshot = [values.copy() for values in batch]
        self.assertEqual(transform_batch(IdentityTransform(), batch), batch)
        self.assertEqual(
            transform_batch(OffsetTransform(2.5), batch),
            [[3.5, 4.5], [], [-0.5]],
        )
        self.assertEqual(batch, snapshot)

    def test_batch_uses_l2_and_clamp_substitutably(self) -> None:
        self.assertEqual(
            transform_batch(ClampTransform(), [[-3.0, 0.5, 2.0], [], [1.0]]),
            [[-1.0, 0.5, 1.0], [], [1.0]],
        )
        output = transform_batch(
            L2NormalizeTransform(), [[3.0, 4.0], [0.0, 0.0], [1.0]]
        )
        self.assert_vector_close(output[0], [0.6, 0.8])
        self.assertEqual(output[1], [0.0, 0.0])
        self.assertEqual(output[2], [1.0])

    def test_chain_applies_steps_in_order(self) -> None:
        chain = TransformChain()
        chain.add_step(ClampTransform())
        chain.add_step(L2NormalizeTransform())
        inverse_norm = 1.0 / math.sqrt(2.0)
        self.assert_vector_close(
            chain.transform([-3.0, 4.0]), [-inverse_norm, inverse_norm]
        )

    def test_chain_is_a_generic_feature_transform(self) -> None:
        chain = TransformChain()
        chain.add_step(OffsetTransform(1.0))
        chain.add_step(OffsetTransform(2.0))
        self.assertIsInstance(chain, FeatureTransform)
        self.assertEqual(FeaturePipeline(chain).run([1.0, -1.0]), [4.0, 2.0])

    def test_empty_chain_returns_a_copy(self) -> None:
        values = [1.0, 2.0]
        output = TransformChain().transform(values)
        self.assertEqual(output, values)
        self.assertIsNot(output, values)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
