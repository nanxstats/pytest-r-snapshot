# AGENTS.md

Guidelines for AI coding agents working on `pytest-r-snapshot`.

## Project overview

- `pytest-r-snapshot` is a pytest plugin that snapshot-tests **Python outputs** against **reference outputs recorded from labelled R code chunks** embedded in Python test files.
- Default workflow is **portable CI**:
  - Developers run `pytest --r-snapshot=record` locally (requires R) and commit snapshot files.
  - CI runs in default `replay` mode (no R required).

## Code layout (keep boundaries)

- `src/pytest_r_snapshot/plugin.py`: pytest integration (options, markers, fixtures).
- `src/pytest_r_snapshot/snapshot.py`: public `RSnapshot` API and snapshot I/O/compare.
- `src/pytest_r_snapshot/chunks.py`: parsing labelled R fenced chunks from Python source.
- `src/pytest_r_snapshot/runner.py`: `RRunner` protocol + subprocess runner (Rscript).
- `src/pytest_r_snapshot/settings.py`: settings dataclass + mode parsing.
- `src/pytest_r_snapshot/errors.py`: custom exceptions with actionable messages.
- `src/pytest_r_snapshot/normalize.py`: generic text normalizers.

Design rule: keep `RSnapshot` as an orchestrator; parsing stays in `chunks`, subprocess logic stays in `runner`, pytest glue stays in `plugin`.

## Development workflow

- Install deps: `uv sync` (requires network).
- Run tests: `.venv/bin/pytest -q`
  - Keep plugin tests hermetic: do **not** require a real R installation.
  - Prefer `pytester` + fake `r_snapshot_runner` overrides for mode behavior tests.
- Lint/type-check (recommended):
  - `.venv/bin/ruff check`
  - `.venv/bin/mypy .`
- Build docs: `.venv/bin/zensical build`

Note: in sandboxed environments, `uv run ...` may fail if `uv` cannot access its global cache; prefer `.venv/bin/...` or set `UV_CACHE_DIR` to a repo-local directory.

## Pytest plugin behavior (don't break)

- Modes: `replay` (default), `record`, `auto`.
- Never run R during collection; only run R when recording is required.
- Snapshot layout must stay stable:
  - Default: `<test_dir>/__r_snapshots__/<test_file_stem>/<name><ext>`
  - If `r_snapshot_dir` is set: `<r_snapshot_dir>/<test_file_stem>/<name><ext>`
- Normalize newlines to `\n` when writing and comparing snapshots.
- Keep error messages actionable (include snapshot path and the re-record command hint).

## Style and typing

- Python >= 3.10, prefer `from __future__ import annotations`.
- Use precise types and small pure helpers; avoid `Any` unless unavoidable.
- Public API must have docstrings and stable signatures:
  - `RSnapshot.read_text`, `record_text`, `assert_match_text`, `path_for`

## Docs hygiene

- Update `README.md` and `docs/` together when user-facing behavior changes.
- Keep zensical nav in `zensical.toml` in sync with `docs/`.
