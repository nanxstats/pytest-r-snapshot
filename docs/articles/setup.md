# Setup

This guide shows how to set up a project to use `pytest-r-snapshot`,
including a recommended CI workflow that does **not** require R.

## Requirements

- Python >= 3.10
- `pytest` (installed automatically as a dependency)
- **R (optional)**:
  - Required for recording snapshots (`--r-snapshot=record` or `--r-snapshot=auto` when a snapshot is missing)
  - Not required for replaying snapshots (the default mode)

## Install

```bash
pip install pytest-r-snapshot
```

Pytest will discover the plugin automatically when it is installed.

## Configure pytest (optional)

All options can be set via command line flags, or in `pyproject.toml` under `[tool.pytest.ini_options]`.

Example configuration:

```toml
[tool.pytest.ini_options]
r_snapshot_mode = "replay"                       # replay|record|auto
r_snapshot_dir = "tests/__r_snapshots__"         # optional custom root
r_snapshot_rscript = "Rscript"                   # or an absolute path
r_snapshot_cwd = "."                             # default: pytest root
r_snapshot_env = ["R_LIBS_USER=/path/to/rlibs"]  # optional, repeatable
r_snapshot_timeout = "30"                        # optional seconds
r_snapshot_encoding = "utf-8"
```

Notes:

- If `r_snapshot_dir` is set, snapshots are written under:
  - `<r_snapshot_dir>/<test_file_stem>/<name><ext>`
- If `r_snapshot_dir` is not set, snapshots are written next to the test file:
  - `<test_dir>/__r_snapshots__/<test_file_stem>/<name><ext>`

## Recording workflow

1. Write tests that embed labelled R chunks (see `docs/articles/usage.md`).
2. Record snapshots locally:

   ```bash
   pytest --r-snapshot=record
   ```

3. Commit the snapshot files to your repository.
4. Run CI in replay mode (default), without requiring R.

`auto` mode is useful for bootstrapping snapshots:

```bash
pytest --r-snapshot=auto
```

## GitHub Actions (CI without R)

The recommended workflow is to run tests in replay mode, relying only on committed snapshots.

```yaml
name: tests

on:
  push:
  pull_request:

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: actions/setup-python@v6
        with:
          python-version: "3.14"
          cache: pip

      - name: Install
        run: |
          python -m pip install -U pip
          python -m pip install -e ".[test]"

      - name: Run tests (replay mode, default)
        run: |
          pytest -q
```

If your project does not define extras, replace the install step with your preferred dependency installer (for example, `pip install -r requirements.txt`).

## CI that records snapshots (optional)

Snapshot recording changes files on disk and is typically done locally and committed.

If you want a **manual** workflow that can regenerate snapshots in CI, you can add a separate job that installs R and runs `pytest --r-snapshot=record`, then uploads the generated snapshots as an artifact for review.
