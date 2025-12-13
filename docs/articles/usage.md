# Usage

`pytest-r-snapshot` records reference outputs from **labelled R code chunks** embedded in your Python test files, then compares your Python outputs to those recorded snapshots.

## Basic fixture usage

Use the `r_snapshot` fixture and compare text output:

```python
def test_summary_matches_r(r_snapshot):
    # ```{r, summary}
    # x <- c(1, 2, 3)
    # summary(x)
    # ```

    actual = my_python_summary(...)
    r_snapshot.assert_match_text(actual, name="summary")
```

Record snapshots locally:

```bash
pytest --r-snapshot=record
```

By default, CI can run `pytest` in replay mode without R.

## Embedding R chunks

### Commented chunks

Commented chunks are convenient when you want the R code to live right above the assertion:

```python
def test_x(r_snapshot):
    # ```{r, label}
    # x <- 1 + 1
    # print(x)
    # ```
    r_snapshot.assert_match_text("2", name="label")
```

Rules:

- Start/end fences must be a standalone line containing three backticks.
- Each body line must start with `#` (an optional single space after `#` is allowed).
- Every chunk must have a **label**, and labels must be unique per file.

### Docstring / multiline string chunks

You can also place raw fenced chunks inside a docstring or multiline string:

```python
def test_summary_matches_r(r_snapshot):
    """
    ```{r, summary}
    x <- c(1, 2, 3)
    summary(x)
    ```
    """
    r_snapshot.assert_match_text(my_python_summary(...), name="summary")
```

The plugin dedents the chunk body to remove Python indentation while keeping relative indentation.

## Snapshot file layout

By default, for `tests/test_example.py`, snapshots are stored under:

`tests/__r_snapshots__/test_example/<name><ext>`

You can override the snapshot root directory with `--r-snapshot-dir` / `r_snapshot_dir`. In that case snapshots are stored under:

`<r_snapshot_dir>/test_example/<name><ext>`

The default file extension is `.txt`. You can change it per assertion:

```python
r_snapshot.assert_match_text(actual, name="minimal_rtf", ext=".rtf")
```

Both `"rtf"` and `".rtf"` are accepted.

## Snapshot modes

- `replay` (default): never runs R; fails if the snapshot is missing.
- `record`: always runs R and overwrites snapshots.
- `auto`: runs R only when a snapshot is missing.

Examples:

```bash
pytest                  # replay
pytest --r-snapshot=auto
pytest --r-snapshot=record
```

## R execution configuration (when recording)

These options matter when the plugin needs to run R (`record` mode, or `auto` with a missing snapshot):

- `--r-snapshot-rscript=PATH` / `r_snapshot_rscript`: which `Rscript` to run
- `--r-snapshot-cwd=PATH` / `r_snapshot_cwd`: working directory for R
- `--r-snapshot-env=KEY=VALUE` / `r_snapshot_env`: environment overrides (repeatable)
- `--r-snapshot-timeout=SECONDS` / `r_snapshot_timeout`: per-chunk timeout
- `--r-snapshot-encoding=ENC` / `r_snapshot_encoding`: snapshot file encoding

See `docs/articles/configuration.md` for the full reference and precedence rules.

## Markers (optional)

You can declare snapshot dependencies at the test boundary:

```python
import pytest

@pytest.mark.r_snapshot("summary")
def test_summary_matches_r(r_snapshot):
    r_snapshot.assert_match_text(my_python_summary(...), name="summary")
```

Or use the decorator alias:

```python
from pytest_r_snapshot import r_snapshot

@r_snapshot("summary")
def test_summary_matches_r(r_snapshot):
    ...
```

The marker is repeatable. It is used for better errors (for example, a test declares snapshot `X` but no chunk `X` exists).

## Normalizing output

The `normalize=` hook lets you apply domain-specific normalization to both expected and actual text before comparison.

Example: normalize newlines and strip trailing whitespace:

```python
from pytest_r_snapshot import normalize_newlines, strip_trailing_whitespace

def normalize(text: str) -> str:
    return strip_trailing_whitespace(normalize_newlines(text))

def test_output(r_snapshot):
    ...
    r_snapshot.assert_match_text(actual, name="out", normalize=normalize)
```

## Reading and recording explicitly

- `r_snapshot.read_text(name="...")` reads a snapshot file (fails if missing).
- `r_snapshot.record_text(name="...")` runs the labelled R chunk and writes the snapshot file.
- `r_snapshot.path_for(name="...")` returns the snapshot path.

## Providing R code explicitly

For advanced use cases, you can pass R code directly via `code=...` to `record_text()` or `assert_match_text()`:

- If `code` contains fenced chunks, the chunk with label `name` is used.
- Otherwise `code` is treated as the raw R body to execute.
