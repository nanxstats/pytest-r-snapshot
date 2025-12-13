from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable

from .errors import RSnapshotError


class SnapshotMode(str, Enum):
    """Whether to replay existing snapshots or record new ones."""

    REPLAY = "replay"
    RECORD = "record"
    AUTO = "auto"

    @classmethod
    def parse(cls, value: str) -> "SnapshotMode":
        """Parse a snapshot mode value from config/CLI."""

        try:
            return cls(value)
        except ValueError as exc:  # pragma: no cover
            choices = ", ".join(sorted(m.value for m in cls))
            raise RSnapshotError(
                f"Invalid r-snapshot mode {value!r}. Choose one of: {choices}."
            ) from exc


@dataclass(frozen=True)
class RSnapshotSettings:
    """Configuration for the r-snapshot plugin."""

    mode: SnapshotMode = SnapshotMode.REPLAY
    snapshot_dir: Path | None = None
    rscript: str = "Rscript"
    cwd: Path | None = None
    env: dict[str, str] = field(default_factory=dict)
    timeout: float | None = None
    encoding: str = "utf-8"


def parse_env_assignments(values: Iterable[str]) -> dict[str, str]:
    """Parse ``KEY=VALUE`` assignments into a dict."""

    parsed: dict[str, str] = {}
    for raw in values:
        if "=" not in raw:
            raise RSnapshotError(
                f"Invalid --r-snapshot-env value {raw!r}; expected KEY=VALUE."
            )
        key, value = raw.split("=", 1)
        key = key.strip()
        if not key:
            raise RSnapshotError(
                f"Invalid --r-snapshot-env value {raw!r}; expected non-empty KEY."
            )
        parsed[key] = value
    return parsed

