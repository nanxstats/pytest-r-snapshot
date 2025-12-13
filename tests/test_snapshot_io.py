from __future__ import annotations

import pytest


def test_default_snapshot_layout(pytester: pytest.Pytester) -> None:
    pytester.makeconftest("pytest_plugins = ['pytest_r_snapshot.plugin']\n")
    pytester.makepyfile(
        test_paths="""
from pathlib import Path

def test_path_for_default_layout(r_snapshot):
    expected = Path(__file__).parent / "__r_snapshots__" / Path(__file__).stem / "hello.txt"
    assert r_snapshot.path_for("hello") == expected
"""
    )
    result = pytester.runpytest_inprocess("-q")
    result.assert_outcomes(passed=1)


def test_read_text_normalizes_newlines(pytester: pytest.Pytester) -> None:
    pytester.makeconftest("pytest_plugins = ['pytest_r_snapshot.plugin']\n")
    pytester.makepyfile(
        test_newlines="""
def test_read_text_normalizes_newlines(r_snapshot):
    path = r_snapshot.path_for("win")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("a\\r\\nb\\r\\n")
    assert r_snapshot.read_text("win") == "a\\nb\\n"
"""
    )
    result = pytester.runpytest_inprocess("-q")
    result.assert_outcomes(passed=1)


def test_ext_is_normalized(pytester: pytest.Pytester) -> None:
    pytester.makeconftest("pytest_plugins = ['pytest_r_snapshot.plugin']\n")
    pytester.makepyfile(
        test_ext="""
def test_ext_is_normalized(r_snapshot):
    assert r_snapshot.path_for("x", ext="rtf") == r_snapshot.path_for("x", ext=".rtf")
"""
    )
    result = pytester.runpytest_inprocess("-q")
    result.assert_outcomes(passed=1)
