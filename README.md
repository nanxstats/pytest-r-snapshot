# pytest-r-snapshot <img src="https://github.com/nanxstats/pytest-r-snapshot/raw/main/docs/assets/logo.png" align="right" width="120" />

[![PyPI version](https://img.shields.io/pypi/v/pytest-r-snapshot)](https://pypi.org/project/pytest-r-snapshot/)
![Python versions](https://img.shields.io/pypi/pyversions/pytest-r-snapshot)
[![CI tests](https://github.com/nanxstats/pytest-r-snapshot/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/nanxstats/pytest-r-snapshot/actions/workflows/ci-tests.yml)
[![Mypy check](https://github.com/nanxstats/pytest-r-snapshot/actions/workflows/mypy.yml/badge.svg)](https://github.com/nanxstats/pytest-r-snapshot/actions/workflows/mypy.yml)
[![Ruff check](https://github.com/nanxstats/pytest-r-snapshot/actions/workflows/ruff-check.yml/badge.svg)](https://github.com/nanxstats/pytest-r-snapshot/actions/workflows/ruff-check.yml)
[![mkdocs](https://github.com/nanxstats/pytest-r-snapshot/actions/workflows/mkdocs.yml/badge.svg)](https://nanx.me/pytest-r-snapshot/)
![License](https://img.shields.io/pypi/l/pytest-r-snapshot)

A pytest plugin for snapshot testing against reference outputs produced by R code.

It is designed for a portable workflow:

- **Record locally (requires R)**: run labelled R chunks embedded in your
  Python tests and write snapshot files.
- **Replay everywhere (default; no R required)**: read committed snapshot
  files and compare them to Python outputs.

The R chunks live close to the test assertion (copy/paste-able from R scripts
or R Markdown), but snapshots are stored as deterministic UTF-8 text files.

## Installation

You can install pytest-r-snapshot from PyPI:

```bash
pip install pytest-r-snapshot
```

If your project is managed with `uv`, add it as a dev dependency:

```bash
uv add --dev pytest-r-snapshot
```

Or install the development version from GitHub:

```bash
git clone https://github.com/nanxstats/pytest-r-snapshot.git
cd pytest-r-snapshot
python3 -m pip install -e .
```

## Quick start

Embed a labelled R fenced chunk (commented or in a docstring),
then compare your Python output to the recorded snapshot:

```python
def test_summary_matches_r(r_snapshot):
    # ```{r, summary}
    # x <- c(1, 2, 3)
    # summary(x)
    # ```

    actual = my_python_summary(...)
    r_snapshot.assert_match_text(actual, name="summary")
```

Generate (or update) snapshots locally:

```bash
pytest --r-snapshot=record
```

Commit the generated snapshot files, and run CI with the default
replay mode (no R required).

## What you get

- A pytest fixture `r_snapshot` with methods:
    - `assert_match_text(actual, name=..., ext=".txt", normalize=...)`
    - `read_text(name=..., ext=".txt")`
    - `record_text(name=..., ext=".txt")`
    - `path_for(name=..., ext=".txt")`
- Snapshot modes: `replay` (default), `record`, `auto`.
- Chunk extraction for R Markdown-style fenced chunks inside Python source:
    - Commented fences (chunk lines prefixed with `#`).
    - Raw chunks in docstrings / multi-line strings.
- Configurable R execution context: `Rscript` path, environment,
  working directory, timeout, encoding.
