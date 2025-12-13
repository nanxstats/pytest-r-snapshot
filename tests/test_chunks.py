from __future__ import annotations

from pathlib import Path

import pytest

from pytest_r_snapshot.chunks import parse_r_chunks
from pytest_r_snapshot.errors import ChunkLabelMissingError, DuplicateChunkLabelError


def test_parse_commented_chunk(pytester: pytest.Pytester) -> None:
    test_file = pytester.makepyfile(
        test_example="""def test_x():
    # ```{r, minimal_rtf}
    # x <- 1 + 1
    # print(x)
    # ```
    assert True
"""
    )

    chunks = parse_r_chunks(Path(str(test_file)))
    assert chunks["minimal_rtf"].code == "x <- 1 + 1\nprint(x)"
    assert chunks["minimal_rtf"].start_line == 2
    assert chunks["minimal_rtf"].end_line == 5


def test_parse_docstring_chunk(pytester: pytest.Pytester) -> None:
    test_file = pytester.makepyfile(
        test_example="""
def test_summary():
    \"\"\"
    ```{r, summary}
    x <- c(1, 2, 3)
    summary(x)
    ```
    \"\"\"
    assert True
"""
    )

    chunks = parse_r_chunks(Path(str(test_file)))
    assert chunks["summary"].code == "x <- c(1, 2, 3)\nsummary(x)"


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("r, label, echo=FALSE", "label"),
        ('r, echo=FALSE, label="quoted"', "quoted"),
        ("r label", "label"),
    ],
)
def test_label_extraction(
    pytester: pytest.Pytester, header: str, expected: str
) -> None:
    test_file = pytester.makepyfile(
        test_example=f"""
def test_x():
    # ```{{{header}}}
    # 1 + 1
    # ```
    assert True
"""
    )
    chunks = parse_r_chunks(Path(str(test_file)))
    assert expected in chunks


def test_missing_label_error(pytester: pytest.Pytester) -> None:
    test_file = pytester.makepyfile(
        test_example="""
def test_x():
    # ```{r}
    # 1 + 1
    # ```
    assert True
"""
    )

    with pytest.raises(ChunkLabelMissingError) as excinfo:
        parse_r_chunks(Path(str(test_file)))
    assert "Chunks must be labelled" in str(excinfo.value)


def test_duplicate_label_error_shows_line_numbers(pytester: pytest.Pytester) -> None:
    test_file = pytester.makepyfile(
        test_example="""def test_x():
    # ```{r, dup}
    # 1 + 1
    # ```
    # ```{r, dup}
    # 2 + 2
    # ```
    assert True
"""
    )

    with pytest.raises(DuplicateChunkLabelError) as excinfo:
        parse_r_chunks(Path(str(test_file)))
    message = str(excinfo.value)
    assert "lines 2, 5" in message
