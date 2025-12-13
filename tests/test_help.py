from __future__ import annotations

import pytest


def test_pytest_help_shows_r_snapshot_options(pytester: pytest.Pytester) -> None:
    pytester.makeconftest("pytest_plugins = ['pytest_r_snapshot.plugin']\n")
    result = pytester.runpytest_inprocess("--help")
    assert "--r-snapshot" in result.stdout.str()
    assert "--r-snapshot-dir" in result.stdout.str()
