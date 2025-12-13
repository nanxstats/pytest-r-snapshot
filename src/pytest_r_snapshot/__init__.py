from __future__ import annotations

from typing import TYPE_CHECKING

from .normalize import normalize_newlines, strip_trailing_whitespace
from .settings import RSnapshotSettings, SnapshotMode
from .snapshot import RSnapshot

if TYPE_CHECKING:  # pragma: no cover
    from _pytest.mark.structures import MarkDecorator


def r_snapshot(name: str, *, ext: str = ".txt") -> MarkDecorator:
    """Decorator alias for :func:`pytest.mark.r_snapshot`.

    This is a small convenience wrapper around the plugin's marker.
    """

    import pytest

    return pytest.mark.r_snapshot(name, ext=ext)


__all__ = [
    "RSnapshot",
    "RSnapshotSettings",
    "SnapshotMode",
    "normalize_newlines",
    "r_snapshot",
    "strip_trailing_whitespace",
]
