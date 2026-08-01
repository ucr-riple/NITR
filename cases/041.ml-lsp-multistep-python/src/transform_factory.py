from __future__ import annotations

from src.clamp_transform import ClampTransform
from src.feature_transform import FeatureTransform
from src.identity_transform import IdentityTransform
from src.l2_normalize_transform import L2NormalizeTransform


def make_transform(name: str) -> FeatureTransform:
    transforms: dict[str, type[FeatureTransform]] = {
        "identity": IdentityTransform,
        "l2": L2NormalizeTransform,
        "clamp": ClampTransform,
    }
    try:
        return transforms[name]()
    except KeyError as exc:
        raise ValueError(f"unknown transform: {name}") from exc
