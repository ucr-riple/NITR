from __future__ import annotations
from src.build_pipeline import build_pipeline
from src.models import Event, PipelineConfig

def main() -> None:
    pipeline = build_pipeline(PipelineConfig())
    print("\n".join(pipeline.runner.run([Event("web", "login ok", 8)])))

if __name__ == "__main__":
    main()
