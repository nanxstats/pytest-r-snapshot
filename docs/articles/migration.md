# Migration guide

This guide outlines how to migrate from an ad hoc "run R chunks and save outputs" approach to `pytest-r-snapshot`.

## Keep your existing R chunks

If your tests already include commented fenced chunks like:

```python
# ```{r, minimal_rtf}
# ...
# ```
```

you can keep them as-is. The plugin uses a compatible chunk syntax and requires only that every chunk has a unique label per file.

## Replace manual readers with the fixture

Instead of custom "expected output" readers, use:

- `r_snapshot.read_text(name="label", ext=".rtf")` to load an expected snapshot
- `r_snapshot.assert_match_text(actual, name="label", ext=".rtf")` to compare with diffs

## Match your existing snapshot directory

If you already store recorded outputs under a specific root, configure the plugin:

```bash
pytest --r-snapshot=record --r-snapshot-dir=vendor/rtflite/tests/fixtures/r_outputs
```

With `--r-snapshot-dir=...`, the plugin writes snapshots under:

`vendor/rtflite/tests/fixtures/r_outputs/<test_file_stem>/<name><ext>`

If your existing layout differs, the simplest migration is to record once with the plugin and commit the new layout.
