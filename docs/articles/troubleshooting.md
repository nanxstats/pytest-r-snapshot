# Troubleshooting

This page covers the most common failures and how to fix them.

## "Snapshot file is missing"

You are in replay mode (default) and the snapshot file does not exist.

Fix:

- Record snapshots locally and commit them:

  ```bash
  pytest --r-snapshot=record
  ```

- Double-check `name=` and `ext=...` match the recorded snapshot filename.
- If you configured `r_snapshot_dir`, confirm the snapshot root is correct.

## "R chunk '...' not found"

The snapshot name you requested does not match any labelled R chunk in the current test file.

Fix:

- Ensure the chunk is labelled and the label matches `name=...`.
- If you use `@pytest.mark.r_snapshot("name")`, the plugin will fail early with a list of available labels.

## "Missing R chunk label"

Every fenced R chunk must have a label.

Accepted examples:

````text
```{r, my_label}
...
```
````

````text
```{r label}
...
```
````

Fix:

- Add a label to the chunk header.

## "Duplicate R chunk label"

Labels must be unique per Python file.

Fix:

- Rename one of the conflicting chunks.

## "Rscript executable not found"

Recording requires `Rscript` to be available.

Fix:

- Install R, or configure the `Rscript` path:

  ```bash
  pytest --r-snapshot=record --r-snapshot-rscript=/path/to/Rscript
  ```

  Or set `r_snapshot_rscript` in `pyproject.toml`.

## "R execution failed"

The R process returned a non-zero exit code. The failure message includes stdout/stderr.

Fix:

- Run in record mode locally to reproduce and inspect the full error:

  ```bash
  pytest --r-snapshot=record -q
  ```

- Verify required R packages are installed and discoverable (for example, set `R_LIBS_USER` via `--r-snapshot-env`).

## Encoding issues

Snapshots are stored as UTF-8 by default.

Fix:

- If you must use a different encoding, set `r_snapshot_encoding` / `--r-snapshot-encoding`.
