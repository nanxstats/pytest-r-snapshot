from __future__ import annotations

from pathlib import Path

import pytest

from pytest_r_snapshot.errors import RscriptNotFoundError
from pytest_r_snapshot.runner import SubprocessRRunner


def test_runner_missing_rscript_gives_helpful_message(tmp_path: Path) -> None:
    runner = SubprocessRRunner(rscript="__definitely_missing_rscript__", cwd=tmp_path)
    with pytest.raises(RscriptNotFoundError) as excinfo:
        runner.run("x <- 1 + 1")
    message = str(excinfo.value)
    assert "Rscript executable not found" in message
    assert "--r-snapshot-rscript" in message
