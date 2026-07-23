#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib
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

from src.cosine_similarity import cosine_similarity


class TupleSequence(Sequence[float]):
    def __init__(self, values: tuple[float, ...]) -> None:
        self._values = values

    def __getitem__(self, index: int) -> float:
        return self._values[index]

    def __len__(self) -> int:
        return len(self._values)


class CosineSimilarityTests(unittest.TestCase):
    def test_computes_cosine_similarity(self) -> None:
        result = cosine_similarity([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
        expected = 32.0 / (math.sqrt(14.0) * math.sqrt(77.0))
        self.assertAlmostEqual(result, expected, places=12)

    def test_handles_orthogonal_and_negative_vectors(self) -> None:
        self.assertEqual(cosine_similarity([1.0, 0.0], [0.0, 2.0]), 0.0)
        self.assertAlmostEqual(
            cosine_similarity([1.0, -1.0], [-1.0, 1.0]), -1.0, places=12
        )

    def test_rejects_size_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            cosine_similarity([1.0], [1.0, 2.0])

    def test_zero_and_empty_vectors_return_zero(self) -> None:
        self.assertEqual(cosine_similarity([0.0, 0.0], [1.0, 2.0]), 0.0)
        self.assertEqual(cosine_similarity([], []), 0.0)

    def test_accepts_general_sequences(self) -> None:
        left = TupleSequence((3.0, 4.0))
        right = (3.0, 4.0)

        self.assertAlmostEqual(cosine_similarity(left, right), 1.0, places=12)

    def test_result_uses_existing_helper_outputs(self) -> None:
        import src.cosine_similarity as cosine_module
        import src.dot_product as dot_module
        import src.l2_norm as norm_module

        original_dot_product = dot_module.dot_product
        original_l2_norm = norm_module.l2_norm
        calls: list[tuple[str, Sequence[float]]] = []
        left = [7.0, 11.0]
        right = [13.0, 17.0]

        def dot_spy(a: Sequence[float], b: Sequence[float]) -> float:
            calls.append(("dot-a", a))
            calls.append(("dot-b", b))
            return 30.0

        def norm_spy(values: Sequence[float]) -> float:
            calls.append(("norm", values))
            if values is left:
                return 2.0
            if values is right:
                return 5.0
            self.fail("l2_norm() received an unexpected sequence")

        try:
            dot_module.dot_product = dot_spy
            norm_module.l2_norm = norm_spy
            cosine_module = importlib.reload(cosine_module)

            result = cosine_module.cosine_similarity(left, right)

            self.assertEqual(result, 3.0)
            self.assertGreaterEqual([name for name, _ in calls].count("dot-a"), 1)
            self.assertGreaterEqual([name for name, _ in calls].count("dot-b"), 1)
            norm_inputs = [values for name, values in calls if name == "norm"]
            self.assertIn(left, norm_inputs)
            self.assertIn(right, norm_inputs)
        finally:
            dot_module.dot_product = original_dot_product
            norm_module.l2_norm = original_l2_norm
            importlib.reload(cosine_module)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
