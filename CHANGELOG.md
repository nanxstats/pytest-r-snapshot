## pytest-r-snapshot 0.1.0

### New features

- Initial release of the `pytest-r-snapshot` pytest plugin for snapshot testing against R code outputs.
- Extract labelled R fenced chunks from Python source (commented chunks and raw chunks in docstrings/multiline strings).
- Snapshot modes: `replay` (default), `record`, and `auto`.
- Default snapshot layout: `__r_snapshots__/<test_file_stem>/<name><ext>` with configurable root via `--r-snapshot-dir` / `r_snapshot_dir`.
- `r_snapshot` fixture with `assert_match_text()`, `read_text()`, `record_text()`, and `path_for()`.
- Configurable R execution: `Rscript` path, env overrides, working directory, timeout, and snapshot encoding.
- Optional marker `@pytest.mark.r_snapshot(...)` and decorator alias `pytest_r_snapshot.r_snapshot(...)`.
- Built-in text normalizers: newline normalization and stripping trailing whitespace.

### Documentation

- Added README and mkdocs articles (setup, usage, configuration, troubleshooting, design, migration).

### Testing

- Added a pytester-based test suite with a mock R runner (no real R required).
