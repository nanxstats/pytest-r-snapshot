from __future__ import annotations


def normalize_newlines(text: str) -> str:
    """Normalize line endings to ``\\n``.

    Snapshot files are stored and compared using Unix newlines for determinism.
    """

    return text.replace("\r\n", "\n").replace("\r", "\n")


def strip_trailing_whitespace(text: str) -> str:
    """Strip trailing spaces and tabs from each line."""

    parts = normalize_newlines(text).split("\n")
    return "\n".join(part.rstrip(" \t") for part in parts)

