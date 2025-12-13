from __future__ import annotations

import difflib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .chunks import RChunk, parse_r_chunks, parse_r_chunks_from_text
from .errors import ChunkNotFoundError, SnapshotNameError, SnapshotNotFoundError
from .normalize import normalize_newlines
from .runner import RRunner
from .settings import RSnapshotSettings, SnapshotMode


@dataclass
class _RSnapshotSession:
    settings: RSnapshotSettings
    rootpath: Path
    runner: RRunner
    _chunk_cache: dict[Path, dict[str, RChunk]] = field(default_factory=dict)

    def chunks_for(self, path: Path) -> dict[str, RChunk]:
        cached = self._chunk_cache.get(path)
        if cached is not None:
            return cached
        parsed = parse_r_chunks(path)
        self._chunk_cache[path] = parsed
        return parsed


class RSnapshot:
    """Snapshot testing against reference outputs recorded from R.

    This object is provided by the ``r_snapshot`` fixture. In replay mode, it reads
    snapshot files and compares them to Python-generated outputs. In record/auto
    modes, it executes the labelled R chunk and writes the snapshot file.
    """

    def __init__(self, *, session: _RSnapshotSession, test_path: Path, nodeid: str) -> None:
        self._session = session
        self._test_path = test_path
        self._nodeid = nodeid

    def read_text(self, name: str, *, ext: str = ".txt") -> str:
        """Read a text snapshot from disk."""

        path = self.path_for(name, ext=ext)
        try:
            text = path.read_text(encoding=self._session.settings.encoding)
        except FileNotFoundError as exc:
            raise SnapshotNotFoundError(self._missing_snapshot_message(path)) from exc
        return normalize_newlines(text)

    def record_text(
        self,
        name: str,
        *,
        ext: str = ".txt",
        code: str | None = None,
    ) -> str:
        """Execute the R code for ``name`` and write its output as a snapshot."""

        r_code = self._resolve_r_code(name, code=code)
        recorded = normalize_newlines(self._session.runner.run(r_code))

        path = self.path_for(name, ext=ext)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open(
            mode="w",
            encoding=self._session.settings.encoding,
            newline="\n",
        ) as handle:
            handle.write(recorded)
        return recorded

    def assert_match_text(
        self,
        actual: str,
        *,
        name: str,
        ext: str = ".txt",
        normalize: Callable[[str], str] | None = None,
        code: str | None = None,
    ) -> None:
        """Assert that ``actual`` matches the expected snapshot content."""

        settings = self._session.settings
        snapshot_path = self.path_for(name, ext=ext)

        match settings.mode:
            case SnapshotMode.REPLAY:
                expected = self.read_text(name, ext=ext)
            case SnapshotMode.RECORD:
                expected = self.record_text(name, ext=ext, code=code)
            case SnapshotMode.AUTO:
                if snapshot_path.exists():
                    expected = self.read_text(name, ext=ext)
                else:
                    expected = self.record_text(name, ext=ext, code=code)
            case _:
                raise AssertionError(f"Unhandled r-snapshot mode: {settings.mode!r}")

        def normalize_both(value: str) -> str:
            value = normalize_newlines(value)
            return normalize(value) if normalize is not None else value

        expected_norm = normalize_both(expected)
        actual_norm = normalize_both(actual)
        if expected_norm == actual_norm:
            return

        diff = "".join(
            difflib.unified_diff(
                expected_norm.splitlines(keepends=True),
                actual_norm.splitlines(keepends=True),
                fromfile=str(snapshot_path),
                tofile="actual",
            )
        )
        raise AssertionError(
            "R snapshot mismatch.\n"
            f"Test: {self._nodeid}\n"
            f"Snapshot: {snapshot_path}\n"
            f"Re-record with: {self._record_command_hint()}\n\n"
            f"{diff}"
        )

    def path_for(self, name: str, *, ext: str = ".txt") -> Path:
        """Return the on-disk path for a snapshot."""

        name = _validate_snapshot_name(name)
        ext = _normalize_ext(ext)

        settings = self._session.settings
        if settings.snapshot_dir is None:
            base_dir = self._test_path.parent / "__r_snapshots__" / self._test_path.stem
        else:
            root = settings.snapshot_dir
            if not root.is_absolute():
                root = self._session.rootpath / root
            base_dir = root / self._test_path.stem

        return base_dir / f"{name}{ext}"

    def _record_command_hint(self) -> str:
        parts = ["pytest", "--r-snapshot=record"]
        snapshot_dir = self._session.settings.snapshot_dir
        if snapshot_dir is not None:
            parts.append(f"--r-snapshot-dir={snapshot_dir}")
        return " ".join(parts)

    def _missing_snapshot_message(self, path: Path) -> str:
        return (
            "Snapshot file is missing.\n"
            f"Snapshot: {path}\n"
            f"Record it with: {self._record_command_hint()}"
        )

    def _resolve_r_code(self, name: str, *, code: str | None) -> str:
        if code is not None:
            if _looks_like_fenced_chunk(code):
                chunks = parse_r_chunks_from_text(code, path=Path("<inline>"))
                if name not in chunks:
                    raise ChunkNotFoundError(
                        path=Path("<inline>"),
                        label=name,
                        available=list(chunks.keys()),
                    )
                return chunks[name].code
            return code

        chunks = self._session.chunks_for(self._test_path)
        if name not in chunks:
            raise ChunkNotFoundError(
                path=self._test_path,
                label=name,
                available=list(chunks.keys()),
            )
        return chunks[name].code


def _normalize_ext(ext: str) -> str:
    ext = ext.strip()
    if not ext:
        return ".txt"
    if not ext.startswith("."):
        ext = f".{ext}"
    return ext


def _validate_snapshot_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise SnapshotNameError("Snapshot name must be a non-empty string.")
    if cleaned in {".", ".."}:
        raise SnapshotNameError(f"Invalid snapshot name: {name!r}.")
    if os.path.sep in cleaned or (os.path.altsep and os.path.altsep in cleaned):
        raise SnapshotNameError(
            f"Snapshot name must not contain path separators: {name!r}."
        )
    return cleaned


def _looks_like_fenced_chunk(text: str) -> bool:
    return "```" in text and "{r" in text
