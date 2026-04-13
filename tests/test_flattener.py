"""Tests for csv_wrangler.flattener."""

from __future__ import annotations

import pytest

from csv_wrangler.flattener import FlattenError, FlattenResult, flatten_rows


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# FlattenResult
# ---------------------------------------------------------------------------


class TestFlattenResult:
    def test_defaults(self):
        r = FlattenResult()
        assert r.input_rows == 0
        assert r.output_rows == 0
        assert r.columns_expanded == []

    def test_custom_values(self):
        r = FlattenResult(input_rows=3, output_rows=7, columns_expanded=["tags"])
        assert r.input_rows == 3
        assert r.output_rows == 7
        assert r.columns_expanded == ["tags"]


# ---------------------------------------------------------------------------
# flatten_rows
# ---------------------------------------------------------------------------


def test_empty_delimiter_raises():
    with pytest.raises(FlattenError, match="delimiter"):
        flatten_rows([], column="tags", delimiter="")


def test_missing_column_raises():
    rows = [_row(name="Alice")]
    it, _ = flatten_rows(rows, column="tags")
    with pytest.raises(FlattenError, match="tags"):
        list(it)


def test_single_value_produces_one_row():
    rows = [_row(name="Alice", tags="python")]
    it, result = flatten_rows(rows, column="tags")
    out = list(it)
    assert len(out) == 1
    assert out[0]["tags"] == "python"
    assert result.input_rows == 1
    assert result.output_rows == 1


def test_multi_value_produces_multiple_rows():
    rows = [_row(name="Alice", tags="python|java|go")]
    it, result = flatten_rows(rows, column="tags")
    out = list(it)
    assert len(out) == 3
    assert [r["tags"] for r in out] == ["python", "java", "go"]
    assert result.input_rows == 1
    assert result.output_rows == 3


def test_other_columns_preserved():
    rows = [_row(id="1", name="Alice", tags="a|b")]
    it, _ = flatten_rows(rows, column="tags")
    out = list(it)
    for row in out:
        assert row["id"] == "1"
        assert row["name"] == "Alice"


def test_multiple_input_rows():
    rows = [
        _row(name="Alice", tags="x|y"),
        _row(name="Bob", tags="z"),
    ]
    it, result = flatten_rows(rows, column="tags")
    out = list(it)
    assert result.input_rows == 2
    assert result.output_rows == 3
    assert len(out) == 3


def test_empty_value_produces_one_row():
    rows = [_row(name="Alice", tags="")]
    it, result = flatten_rows(rows, column="tags")
    out = list(it)
    assert len(out) == 1
    assert out[0]["tags"] == ""
    assert result.output_rows == 1


def test_custom_delimiter():
    rows = [_row(name="Alice", tags="a,b,c")]
    it, result = flatten_rows(rows, column="tags", delimiter=",")
    out = list(it)
    assert len(out) == 3
    assert result.output_rows == 3


def test_columns_expanded_recorded():
    rows = [_row(x="a|b")]
    it, result = flatten_rows(rows, column="x")
    list(it)
    assert result.columns_expanded == ["x"]


def test_empty_input_produces_no_rows():
    it, result = flatten_rows([], column="tags")
    assert list(it) == []
    assert result.input_rows == 0
    assert result.output_rows == 0
