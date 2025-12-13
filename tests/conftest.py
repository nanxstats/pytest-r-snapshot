from __future__ import annotations

import pytest

pytest_plugins = ["pytester"]


@pytest.fixture(autouse=True)
def _disable_external_pytest_plugins(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid interference from globally installed pytest plugins in pytester runs."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
