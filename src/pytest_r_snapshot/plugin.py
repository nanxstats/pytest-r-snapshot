from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from .errors import RSnapshotError
from .errors import ChunkNotFoundError
from .runner import SubprocessRRunner
from .settings import RSnapshotSettings, SnapshotMode, parse_env_assignments
from .snapshot import RSnapshot, _RSnapshotSession


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("r-snapshot")

    group.addoption(
        "--r-snapshot",
        dest="r_snapshot_mode",
        default=None,
        choices=[m.value for m in SnapshotMode],
        help="R snapshot mode: replay|record|auto (default: replay)",
    )
    group.addoption(
        "--r-snapshot-record",
        action="store_const",
        const=SnapshotMode.RECORD.value,
        dest="r_snapshot_mode",
        help="Shortcut for --r-snapshot=record.",
    )
    group.addoption(
        "--r-snapshot-auto",
        action="store_const",
        const=SnapshotMode.AUTO.value,
        dest="r_snapshot_mode",
        help="Shortcut for --r-snapshot=auto.",
    )
    group.addoption(
        "--r-snapshot-dir",
        dest="r_snapshot_dir",
        default=None,
        help="Root directory for storing snapshots.",
        metavar="PATH",
    )
    group.addoption(
        "--r-snapshot-rscript",
        dest="r_snapshot_rscript",
        default=None,
        help="Path to the Rscript executable (default: Rscript).",
        metavar="PATH",
    )
    group.addoption(
        "--r-snapshot-cwd",
        dest="r_snapshot_cwd",
        default=None,
        help="Working directory for R execution (default: pytest root).",
        metavar="PATH",
    )
    group.addoption(
        "--r-snapshot-env",
        dest="r_snapshot_env",
        default=None,
        action="append",
        help="Environment override (KEY=VALUE). Can be passed multiple times.",
        metavar="KEY=VALUE",
    )
    group.addoption(
        "--r-snapshot-timeout",
        dest="r_snapshot_timeout",
        default=None,
        type=float,
        help="Timeout for each Rscript call (seconds).",
        metavar="SECONDS",
    )
    group.addoption(
        "--r-snapshot-encoding",
        dest="r_snapshot_encoding",
        default=None,
        help="Snapshot file encoding (default: utf-8).",
        metavar="ENC",
    )

    parser.addini(
        "r_snapshot_mode",
        "R snapshot mode: replay|record|auto",
        default=SnapshotMode.REPLAY.value,
    )
    parser.addini("r_snapshot_dir", "Root directory for storing snapshots.", default="")
    parser.addini(
        "r_snapshot_rscript",
        "Path to the Rscript executable.",
        default="Rscript",
    )
    parser.addini(
        "r_snapshot_cwd",
        "Working directory for R execution.",
        default="",
    )
    parser.addini(
        "r_snapshot_env",
        "Environment overrides for R execution (KEY=VALUE).",
        type="linelist",
        default=[],
    )
    parser.addini(
        "r_snapshot_timeout",
        "Timeout for each Rscript call (seconds).",
        default="",
    )
    parser.addini(
        "r_snapshot_encoding",
        "Snapshot file encoding.",
        default="utf-8",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        'r_snapshot(name, ext=".txt"): declare R snapshot dependencies',
    )


@pytest.fixture(scope="session")
def r_snapshot_settings(pytestconfig: pytest.Config) -> RSnapshotSettings:
    """Session-scoped settings hook for configuring r-snapshot.

    Users may override this fixture in ``conftest.py`` to provide custom defaults.
    CLI options still take precedence over this fixture.
    """

    ini_mode = str(pytestconfig.getini("r_snapshot_mode") or SnapshotMode.REPLAY.value)
    mode = SnapshotMode.parse(ini_mode)

    ini_dir = str(pytestconfig.getini("r_snapshot_dir") or "")
    snapshot_dir = Path(ini_dir) if ini_dir else None

    rscript = str(pytestconfig.getini("r_snapshot_rscript") or "Rscript")

    ini_cwd = str(pytestconfig.getini("r_snapshot_cwd") or "")
    cwd = Path(ini_cwd) if ini_cwd else None

    env_list = pytestconfig.getini("r_snapshot_env") or []
    env = parse_env_assignments(env_list)

    timeout_raw = str(pytestconfig.getini("r_snapshot_timeout") or "").strip()
    timeout = float(timeout_raw) if timeout_raw else None

    encoding = str(pytestconfig.getini("r_snapshot_encoding") or "utf-8")

    return RSnapshotSettings(
        mode=mode,
        snapshot_dir=snapshot_dir,
        rscript=rscript,
        cwd=cwd,
        env=env,
        timeout=timeout,
        encoding=encoding,
    )


@pytest.fixture(scope="session")
def r_snapshot_effective_settings(
    pytestconfig: pytest.Config, r_snapshot_settings: RSnapshotSettings
) -> RSnapshotSettings:
    """Effective settings after applying CLI overrides."""

    settings = r_snapshot_settings
    try:
        cli_mode = pytestconfig.getoption("r_snapshot_mode")
        if cli_mode is not None:
            settings = replace(settings, mode=SnapshotMode.parse(str(cli_mode)))

        cli_dir = pytestconfig.getoption("r_snapshot_dir")
        if cli_dir is not None:
            settings = replace(settings, snapshot_dir=Path(str(cli_dir)))

        cli_rscript = pytestconfig.getoption("r_snapshot_rscript")
        if cli_rscript is not None:
            settings = replace(settings, rscript=str(cli_rscript))

        cli_cwd = pytestconfig.getoption("r_snapshot_cwd")
        if cli_cwd is not None:
            settings = replace(settings, cwd=Path(str(cli_cwd)))

        cli_env = pytestconfig.getoption("r_snapshot_env")
        if cli_env:
            merged_env = dict(settings.env)
            merged_env.update(parse_env_assignments(cli_env))
            settings = replace(settings, env=merged_env)

        cli_timeout = pytestconfig.getoption("r_snapshot_timeout")
        if cli_timeout is not None:
            settings = replace(settings, timeout=float(cli_timeout))

        cli_encoding = pytestconfig.getoption("r_snapshot_encoding")
        if cli_encoding is not None:
            settings = replace(settings, encoding=str(cli_encoding))
    except RSnapshotError as exc:
        raise pytest.UsageError(str(exc)) from exc

    return settings


@pytest.fixture(scope="session")
def r_snapshot_runner(
    pytestconfig: pytest.Config, r_snapshot_effective_settings: RSnapshotSettings
):
    """Runner used to execute R code (overridable for tests)."""

    settings = r_snapshot_effective_settings
    cwd = settings.cwd or pytestconfig.rootpath
    if not cwd.is_absolute():
        cwd = pytestconfig.rootpath / cwd
    return SubprocessRRunner(
        rscript=settings.rscript,
        cwd=cwd,
        env_overrides=settings.env,
        timeout=settings.timeout,
    )


@pytest.fixture(scope="session")
def r_snapshot_session(
    pytestconfig: pytest.Config,
    r_snapshot_effective_settings: RSnapshotSettings,
    r_snapshot_runner,
) -> _RSnapshotSession:
    return _RSnapshotSession(
        settings=r_snapshot_effective_settings,
        rootpath=pytestconfig.rootpath,
        runner=r_snapshot_runner,
    )


@pytest.fixture()
def r_snapshot(request: pytest.FixtureRequest, r_snapshot_session: _RSnapshotSession) -> RSnapshot:
    test_path = getattr(request.node, "path", None)
    if test_path is None:  # pragma: no cover
        test_path = Path(str(request.node.fspath))
    else:
        test_path = Path(str(test_path))
    snapshot = RSnapshot(session=r_snapshot_session, test_path=test_path, nodeid=request.node.nodeid)

    declared = []
    for marker in request.node.iter_markers("r_snapshot"):
        if marker.args:
            declared.append(marker.args[0])
        elif "name" in marker.kwargs:
            declared.append(marker.kwargs["name"])
    if declared:
        chunks = r_snapshot_session.chunks_for(test_path)
        for name in declared:
            if not isinstance(name, str):
                raise pytest.UsageError(
                    "r_snapshot marker expects a snapshot name as a string."
                )
            if name not in chunks:
                raise ChunkNotFoundError(
                    path=test_path, label=name, available=list(chunks.keys())
                )

    return snapshot
