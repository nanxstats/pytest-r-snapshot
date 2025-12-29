from __future__ import annotations

import os
from pathlib import Path

import pytest

from pytest_r_snapshot.errors import RExecutionError, RscriptNotFoundError
from pytest_r_snapshot.runner import SubprocessRRunner


def _make_sleeping_rscript(tmp_path: Path) -> Path:
    rscript_path = tmp_path / "Rscript"
    rscript_path.write_text("#!/bin/sh\n/bin/sleep 5\n", encoding="utf-8")
    rscript_path.chmod(rscript_path.stat().st_mode | 0o111)
    return rscript_path


def test_runner_missing_rscript_gives_helpful_message(tmp_path: Path) -> None:
    runner = SubprocessRRunner(rscript="__definitely_missing_rscript__", cwd=tmp_path)
    with pytest.raises(RscriptNotFoundError) as excinfo:
        runner.run("x <- 1 + 1")
    message = str(excinfo.value)
    assert "Rscript executable not found" in message
    assert "--r-snapshot-rscript" in message


@pytest.mark.skipif(os.name == "nt", reason="relies on POSIX executable scripts")
def test_runner_timeout_raises_execution_error(tmp_path: Path) -> None:
    rscript = _make_sleeping_rscript(tmp_path)
    runner = SubprocessRRunner(rscript=str(rscript), cwd=tmp_path, timeout=0.5)
    with pytest.raises(RExecutionError, match="timed out"):
        runner.run("Sys.sleep(5)")
