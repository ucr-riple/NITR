from __future__ import annotations

import math
from collections.abc import Sequence


def l2_norm(values: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in values))
