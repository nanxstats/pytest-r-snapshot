from __future__ import annotations

import pytest


def test_replay_fails_when_snapshot_missing(pytester: pytest.Pytester) -> None:
    pytester.makeconftest("pytest_plugins = ['pytest_r_snapshot.plugin']\n")
    pytester.makepyfile(
        test_missing="""
def test_missing_snapshot(r_snapshot):
    r_snapshot.assert_match_text("anything", name="missing")
"""
    )
    result = pytester.runpytest_inprocess("-q")
    result.assert_outcomes(failed=1)
    out = result.stdout.str()
    assert "--r-snapshot=record" in out
    assert "Snapshot file is missing" in out


def test_auto_records_when_snapshot_missing(pytester: pytest.Pytester) -> None:
    pytester.makeconftest(
        """
import pytest

pytest_plugins = ['pytest_r_snapshot.plugin']

class FakeRunner:
    def run(self, code: str) -> str:
        return "expected"

@pytest.fixture(scope="session")
def r_snapshot_runner():
    return FakeRunner()
"""
    )
    pytester.makepyfile(
        test_auto="""
def test_auto_records(r_snapshot):
    # ```{r, foo}
    # cat("expected")
    # ```
    r_snapshot.assert_match_text("expected", name="foo")
"""
    )

    result = pytester.runpytest_inprocess("-q", "--r-snapshot=auto")
    result.assert_outcomes(passed=1)

    snapshot_path = pytester.path / "__r_snapshots__" / "test_auto" / "foo.txt"
    assert snapshot_path.read_text(encoding="utf-8") == "expected"


def test_record_overwrites_snapshot(pytester: pytest.Pytester) -> None:
    pytester.makeconftest(
        """
import pytest

pytest_plugins = ['pytest_r_snapshot.plugin']

class FakeRunner:
    def run(self, code: str) -> str:
        return "new"

@pytest.fixture(scope="session")
def r_snapshot_runner():
    return FakeRunner()
"""
    )
    pytester.makepyfile(
        test_record="""
def test_record_overwrites(r_snapshot):
    # ```{r, foo}
    # cat("new")
    # ```
    r_snapshot.assert_match_text("new", name="foo")
"""
    )

    snapshot_path = pytester.path / "__r_snapshots__" / "test_record" / "foo.txt"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("old", encoding="utf-8")

    result = pytester.runpytest_inprocess("-q", "--r-snapshot=record")
    result.assert_outcomes(passed=1)
    assert snapshot_path.read_text(encoding="utf-8") == "new"
