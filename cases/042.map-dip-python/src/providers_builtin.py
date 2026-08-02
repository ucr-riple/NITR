from __future__ import annotations

from src.map_snapshot import GLOBAL_LAYER_REGISTRY, LayerProvider


class GeometryProvider(LayerProvider):
    @property
    def name(self) -> str:
        return "geometry"

    def build_layer(self, payload: str) -> str:
        count = sum(character.isalnum() for character in payload)
        return f"alnum_count={count}"


class SemanticsProvider(LayerProvider):
    @property
    def name(self) -> str:
        return "semantics"

    def build_layer(self, payload: str) -> str:
        tokens = payload.split()
        first_token = tokens[0][:16] if tokens else "EMPTY"
        return f"first_token={first_token}"


def register_builtin_layer_providers() -> None:
    GLOBAL_LAYER_REGISTRY.register("geometry", lambda _: GeometryProvider())
    GLOBAL_LAYER_REGISTRY.register("semantics", lambda _: SemanticsProvider())
