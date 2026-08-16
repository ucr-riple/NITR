"""Common interface implemented by NITR submission backends."""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from collections.abc import Mapping


class Backend(ABC):
    """Thin interface for backend registration and dispatch."""

    name: str
    defaults: Mapping[str, object]

    @abstractmethod
    def run(self, args: argparse.Namespace) -> None:
        """Run one submission using parsed command-line arguments."""
