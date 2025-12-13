from __future__ import annotations

from pathlib import Path


class RSnapshotError(Exception):
    """Base exception for pytest-r-snapshot."""


class ChunkParseError(RSnapshotError):
    """Raised when parsing R chunks from a source file fails."""


class ChunkLabelMissingError(ChunkParseError):
    """Raised when an R fenced chunk is missing a required label."""

    def __init__(self, *, path: Path, line: int, header: str) -> None:
        message = (
            f"Missing R chunk label in {path}:{line}.\n\n"
            "Chunks must be labelled, for example:\n\n"
            "    ```{r, my_label}\n"
            "    x <- 1 + 1\n"
            "    print(x)\n"
            "    ```\n\n"
            f"Found header: {{{header}}}"
        )
        super().__init__(message)


class DuplicateChunkLabelError(ChunkParseError):
    """Raised when a Python file contains duplicate R chunk labels."""

    def __init__(self, *, path: Path, label: str, lines: list[int]) -> None:
        lines_str = ", ".join(str(line) for line in sorted(lines))
        super().__init__(
            f"Duplicate R chunk label {label!r} in {path}: lines {lines_str}."
        )


class UnclosedChunkError(ChunkParseError):
    """Raised when an R fenced chunk start fence has no matching end fence."""

    def __init__(self, *, path: Path, label: str, start_line: int) -> None:
        message = (
            f"Unclosed R chunk {label!r} in {path}:{start_line}: "
            "missing closing ``` fence."
        )
        super().__init__(message)


class ChunkNotFoundError(RSnapshotError):
    """Raised when an expected R chunk label cannot be found."""

    def __init__(self, *, path: Path, label: str, available: list[str]) -> None:
        available_str = ", ".join(repr(x) for x in sorted(available)) or "(none found)"
        super().__init__(
            f"R chunk {label!r} not found in {path}. Available labels: {available_str}."
        )


class SnapshotNameError(RSnapshotError):
    """Raised when a snapshot name is invalid for use as a filename."""


class SnapshotNotFoundError(RSnapshotError):
    """Raised when a snapshot file is missing in replay mode."""


class RscriptNotFoundError(RSnapshotError):
    """Raised when the configured Rscript executable cannot be found."""


class RExecutionError(RSnapshotError):
    """Raised when an R chunk execution fails."""
