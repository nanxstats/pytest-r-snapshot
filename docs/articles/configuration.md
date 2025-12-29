# Configuration

This page lists configuration options for pytest-r-snapshot and how they are resolved.

## Snapshot mode

Controls whether snapshots are read from disk or recorded by running R:

- CLI: `--r-snapshot={replay,record,auto}`
    - Aliases: `--r-snapshot-record`, `--r-snapshot-auto`
- Ini: `r_snapshot_mode`
- Default: `replay`

## Snapshot directory

Controls where snapshot files are stored:

- CLI: `--r-snapshot-dir=PATH`
- Ini: `r_snapshot_dir`
- Default: `<test_dir>/__r_snapshots__/<test_file_stem>/...`

When `r_snapshot_dir` is set, snapshots are written under:

```text
<r_snapshot_dir>/<test_file_stem>/<name><ext>
```

## R execution options

These are only used when recording is required (`record` mode, or `auto` mode with a missing snapshot).

### Rscript executable

- CLI: `--r-snapshot-rscript=PATH`
- Ini: `r_snapshot_rscript`
- Default: `Rscript`

### Working directory

- CLI: `--r-snapshot-cwd=PATH`
- Ini: `r_snapshot_cwd`
- Default: pytest root directory

### Environment variables

- CLI: `--r-snapshot-env=KEY=VALUE` (repeatable)
- Ini: `r_snapshot_env` (a list of `KEY=VALUE` lines)
- Default: no overrides (inherits the current environment)

Example:

```bash
pytest --r-snapshot=record --r-snapshot-env=R_LIBS_USER=/path/to/rlibs
```

### Timeout

- CLI: `--r-snapshot-timeout=SECONDS`
- Ini: `r_snapshot_timeout`
- Default: no timeout

### Snapshot encoding

- CLI: `--r-snapshot-encoding=ENC`
- Ini: `r_snapshot_encoding`
- Default: `utf-8`

## Configuration precedence

Settings are resolved in this order (highest wins):

1. CLI options
2. `r_snapshot_settings` fixture (if you override it in `conftest.py`)
3. `pyproject.toml` / ini configuration
4. Built-in defaults

## `conftest.py` hook (advanced)

You can override the session-scoped `r_snapshot_settings` fixture to compute defaults dynamically:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from pytest_r_snapshot import RSnapshotSettings, SnapshotMode


@pytest.fixture(scope="session")
def r_snapshot_settings() -> RSnapshotSettings:
    return RSnapshotSettings(
        mode=SnapshotMode.REPLAY,
        snapshot_dir=Path("tests/fixtures/r_outputs"),
        rscript="Rscript",
        env={"R_LIBS_USER": "/path/to/rlibs"},
        timeout=30,
        encoding="utf-8",
    )
```

CLI flags still override this fixture.

!!! note
    The `r_snapshot_runner` fixture is session-scoped, so a single `Rscript`
    configuration is used for the entire test session.
    If you need different R environments, run separate pytest invocations
    with different settings (for example, vary `--r-snapshot-rscript` or
    `--r-snapshot-env`).
