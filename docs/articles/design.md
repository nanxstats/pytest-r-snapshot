# Design

`pytest-r-snapshot` is intentionally small and modular. The public API is the `r_snapshot` fixture (an `RSnapshot` instance) and a few helpers; everything else is internal plumbing to keep parsing, subprocess execution, and snapshot I/O isolated and testable.

## High-level flow

When a test calls `r_snapshot.assert_match_text(...)`:

1. The snapshot file path is resolved for `(test_file, name, ext)`.
2. The expected value is obtained based on the configured mode:
    - `replay`: read the snapshot file
    - `record`: run R and rewrite the snapshot file
    - `auto`: record only if the snapshot file is missing
3. Expected and actual are newline-normalized (and optionally user-normalized).
4. If they differ, pytest-friendly unified diff output is included in the failure message.

## Module responsibilities

The implementation follows a "thin orchestrator" pattern:

- `pytest_r_snapshot/chunks.py`
    - Parses labelled R fenced chunks from Python source files.
    - Scans line-by-line and tracks `start_line`/`end_line` for diagnostics.
    - Supports both commented chunks and raw chunks in docstrings/multiline strings.
- `pytest_r_snapshot/runner.py`
    - Defines the `RRunner` protocol and a subprocess implementation.
    - Runs `Rscript --vanilla <tempfile.R>` and returns captured stdout.
    - Wraps user code in a minimal R template using `capture.output({ ... })` for deterministic text snapshots.
- `pytest_r_snapshot/snapshot.py`
    - Implements the public `RSnapshot` class.
    - Resolves snapshot paths, reads/writes snapshot files, and performs comparisons.
    - Delegates parsing to `chunks` and execution to an `RRunner`.
- `pytest_r_snapshot/settings.py`
    - Defines settings (`RSnapshotSettings`) and `SnapshotMode`, plus parsing helpers.
- `pytest_r_snapshot/plugin.py`
    - Integrates with pytest: CLI/ini options, marker registration, and fixtures.
    - Builds effective settings using the precedence model: CLI overrides everything; a `conftest.py` settings fixture can override ini defaults.
- `pytest_r_snapshot/errors.py`
    - Custom exception types for clear, targeted error messages.
- `pytest_r_snapshot/normalize.py`
    - Small, generic normalization helpers (newline normalization, trimming).

## Configuration precedence

Settings are merged in this order:

1. Built-in defaults
2. `pyproject.toml` / pytest ini values
3. A user-provided `r_snapshot_settings` fixture (session-scoped) in `conftest.py`
4. CLI options (highest precedence)

This allows project-wide defaults to live in version control while still letting developers override behavior locally via CLI.

## Testing strategy

The plugin's own tests are hermetic and do not require R:

- Chunk parsing and path resolution are unit-tested directly.
- Mode behavior is tested using `pytester` and a fake `RRunner` provided by overriding the `r_snapshot_runner` session fixture.
- A small contract test verifies that the subprocess runner raises a helpful error when `Rscript` is missing.

This keeps CI fast and avoids coupling plugin correctness to a specific R installation.
