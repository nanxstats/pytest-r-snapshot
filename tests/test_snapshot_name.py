from __future__ import annotations

import os

import pytest

from pytest_r_snapshot.errors import SnapshotNameError
from pytest_r_snapshot.snapshot import _validate_snapshot_name


def _path_traversal_names() -> list[str]:
    sep = os.path.sep
    altsep = os.path.altsep
    names = [
        "../../../etc/passwd",
        f"..{sep}..{sep}etc{sep}passwd",
        f"subdir{sep}file",
        f"{sep}etc{sep}passwd",
    ]
    if altsep and altsep != sep:
        names.extend(
            [
                f"..{altsep}..{altsep}etc{altsep}passwd",
                f"subdir{altsep}file",
                f"{altsep}etc{altsep}passwd",
            ]
        )
    return list(dict.fromkeys(names))


@pytest.mark.parametrize("name", _path_traversal_names())
def test_snapshot_name_rejects_path_traversal(name: str) -> None:
    with pytest.raises(SnapshotNameError):
        _validate_snapshot_name(name)
