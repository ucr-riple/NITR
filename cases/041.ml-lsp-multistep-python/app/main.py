from __future__ import annotations

from src.feature_pipeline import FeaturePipeline
from src.transform_factory import make_transform


def main() -> None:
    pipeline = FeaturePipeline(make_transform("identity"))
    print(pipeline.run([1.0, 2.0, 3.0]))


if __name__ == "__main__":
    main()
