from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Mapping, Protocol

from .errors import RExecutionError, RscriptNotFoundError


class RRunner(Protocol):
    """Execute R code and return captured stdout."""

    def run(self, code: str) -> str:
        """Run R code and return captured output as text."""


class SubprocessRRunner:
    """Execute R code via ``Rscript`` using :mod:`subprocess`."""

    def __init__(
        self,
        *,
        rscript: str,
        cwd: Path,
        env_overrides: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> None:
        self._rscript = rscript
        self._cwd = cwd
        env = dict(os.environ)
        if env_overrides:
            env.update(env_overrides)
        self._env = env
        self._timeout = timeout

    def run(self, code: str) -> str:
        script = _render_script(code)
        script_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".R",
                encoding="utf-8",
                newline="\n",
                delete=False,
            ) as handle:
                script_path = Path(handle.name)
                handle.write(script)

            cmd = [self._rscript, "--vanilla", str(script_path)]
            try:
                completed = subprocess.run(
                    cmd,
                    cwd=str(self._cwd),
                    env=self._env,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                    check=False,
                )
            except FileNotFoundError as exc:
                raise RscriptNotFoundError(
                    f"Rscript executable not found: {self._rscript!r}.\n"
                    "Configure it via --r-snapshot-rscript=PATH or r_snapshot_rscript."
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise RExecutionError(
                    f"Rscript timed out after {self._timeout} seconds.\n"
                    f"Command: {' '.join(cmd)}"
                ) from exc

            if completed.returncode != 0:
                stderr = (completed.stderr or "").strip()
                stdout = (completed.stdout or "").strip()
                details = []
                if stdout:
                    details.append(f"stdout:\n{stdout}")
                if stderr:
                    details.append(f"stderr:\n{stderr}")
                details_str = "\n\n".join(details) or "(no output)"
                raise RExecutionError(
                    "R execution failed.\n"
                    f"Command: {' '.join(cmd)}\n"
                    f"Exit code: {completed.returncode}\n\n"
                    f"{details_str}"
                )

            return completed.stdout
        finally:
            if script_path is not None:
                try:
                    script_path.unlink(missing_ok=True)
                except OSError:
                    pass


def _render_script(user_code: str) -> str:
    return (
        "options(width = 200)\n"
        "out <- capture.output({\n"
        f"{user_code}\n"
        "})\n"
        'cat(paste(out, collapse = "\\n"))\n'
    )

