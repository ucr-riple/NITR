from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class LayerProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable layer name."""

    @abstractmethod
    def build_layer(self, payload: str) -> str:
        """Build this layer from the input payload."""


LayerCreator = Callable[[dict[str, Any]], LayerProvider]


class LayerRegistry:
    def __init__(self) -> None:
        self._creators: dict[str, LayerCreator] = {}

    def register(self, layer_type: str, creator: LayerCreator) -> None:
        if layer_type:
            self._creators[layer_type] = creator

    def create(self, layer_config: dict[str, Any]) -> LayerProvider:
        layer_type = layer_config.get("type")
        if not isinstance(layer_type, str):
            raise ValueError("each layer must contain a string type")
        try:
            return self._creators[layer_type](layer_config)
        except KeyError as exc:
            raise ValueError(f"unknown layer type: {layer_type}") from exc


GLOBAL_LAYER_REGISTRY = LayerRegistry()


class MapSnapshotService:
    def build_snapshot(self, config: dict[str, Any], payload: str) -> str:
        from src.providers_builtin import GeometryProvider, SemanticsProvider

        layers = config.get("layers")
        if not isinstance(layers, list):
            raise ValueError("config must contain a layers array")
        output = ["SNAPSHOT"]
        for layer_config in layers:
            if not isinstance(layer_config, dict):
                raise ValueError("each layer must be an object")
            layer_type = layer_config.get("type")
            if layer_type == "geometry":
                provider: LayerProvider = GeometryProvider()
            elif layer_type == "semantics":
                provider = SemanticsProvider()
            else:
                raise ValueError(f"unknown layer type: {layer_type}")
            output.append(f"{provider.name}:{provider.build_layer(payload)}")
        return "\n".join(output) + "\n"
