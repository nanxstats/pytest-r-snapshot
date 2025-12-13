from __future__ import annotations

import re
import textwrap
import tokenize
from dataclasses import dataclass
from pathlib import Path

from .errors import (
    ChunkLabelMissingError,
    ChunkParseError,
    DuplicateChunkLabelError,
    UnclosedChunkError,
)

_START_FENCE_RE = re.compile(r"^```\s*\{([^}]*)\}\s*$")
_END_FENCE_RE = re.compile(r"^```\s*$")
_LABEL_KV_RE = re.compile(
    r"""(?x)
    \blabel
    \s*=\s*
    (?:
        " (?P<dq> [^"]+ ) "
        |
        ' (?P<sq> [^']+ ) '
        |
        (?P<bare> [^,\s]+ )
    )
    """
)


@dataclass(frozen=True)
class RChunk:
    """A labelled R chunk extracted from a Python source file."""

    label: str
    code: str
    path: Path
    start_line: int
    end_line: int


def parse_r_chunks(path: Path) -> dict[str, RChunk]:
    """Parse labelled R fenced chunks from a Python source file."""

    with tokenize.open(path) as handle:
        source = handle.read()
    return parse_r_chunks_from_text(source, path=path)


def parse_r_chunks_from_text(source: str, *, path: Path) -> dict[str, RChunk]:
    """Parse labelled R fenced chunks from source text."""

    lines = source.splitlines()
    chunks: dict[str, RChunk] = {}
    label_to_lines: dict[str, list[int]] = {}

    line_index = 0
    while line_index < len(lines):
        raw_line = lines[line_index]
        stripped, is_commented = _strip_comment_prefix(raw_line)
        header = _parse_start_fence_header(stripped)
        if header is None:
            line_index += 1
            continue

        start_line = line_index + 1
        label = _extract_label(header, path=path, line=start_line)

        body_lines: list[str] = []
        line_index += 1
        while line_index < len(lines):
            raw_body_line = lines[line_index]
            body_stripped, _ = _strip_comment_prefix(raw_body_line)
            if _END_FENCE_RE.match(body_stripped) is not None:
                end_line = line_index + 1
                code = _normalize_body(body_lines, commented=is_commented)
                chunk = RChunk(
                    label=label,
                    code=code,
                    path=path,
                    start_line=start_line,
                    end_line=end_line,
                )
                chunks[label] = chunk
                label_to_lines.setdefault(label, []).append(start_line)
                break
            body_lines.append(raw_body_line)
            line_index += 1
        else:
            raise UnclosedChunkError(path=path, label=label, start_line=start_line)

        line_index += 1

    duplicates = {k: v for k, v in label_to_lines.items() if len(v) > 1}
    if duplicates:
        label, dup_lines = sorted(duplicates.items(), key=lambda kv: kv[0])[0]
        raise DuplicateChunkLabelError(path=path, label=label, lines=dup_lines)

    return chunks


def _strip_comment_prefix(line: str) -> tuple[str, bool]:
    stripped = line.lstrip()
    if not stripped.startswith("#"):
        return stripped, False
    stripped = stripped[1:]
    if stripped.startswith(" "):
        stripped = stripped[1:]
    return stripped, True


def _parse_start_fence_header(line: str) -> str | None:
    if not line.startswith("```") or line.startswith("````"):
        return None
    match = _START_FENCE_RE.match(line)
    if match is None:
        return None
    header = match.group(1).strip()
    if not header.startswith("r") or (len(header) > 1 and header[1] not in (" ", ",")):
        return None
    return header


def _extract_label(header: str, *, path: Path, line: int) -> str:
    label_match = _LABEL_KV_RE.search(header)
    if label_match is not None:
        label = label_match.group("dq") or label_match.group("sq") or label_match.group(
            "bare"
        )
        return label.strip()

    tokens = header.replace(",", " ").split()
    if not tokens or tokens[0] != "r":
        raise ChunkLabelMissingError(path=path, line=line, header=header)

    for token in tokens[1:]:
        if token and "=" not in token:
            return token.strip().strip("'\"")

    raise ChunkLabelMissingError(path=path, line=line, header=header)


def _normalize_body(body_lines: list[str], *, commented: bool) -> str:
    if not body_lines:
        return ""
    if commented:
        normalized: list[str] = []
        for raw in body_lines:
            if raw.strip() == "":
                normalized.append("")
                continue
            stripped = raw.lstrip()
            if not stripped.startswith("#"):
                raise ChunkParseError(
                    "Found a non-comment line inside a commented R chunk body. "
                    "Commented chunks must prefix each line with '#'."
                )
            stripped = stripped[1:]
            if stripped.startswith(" "):
                stripped = stripped[1:]
            normalized.append(stripped)
        return "\n".join(normalized)

    return textwrap.dedent("\n".join(body_lines))
