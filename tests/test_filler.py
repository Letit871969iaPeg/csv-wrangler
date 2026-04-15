"""Tests for csv_wrangler.filler."""
from __future__ import annotations

import pytest

from csv_wrangler.filler import FillError, FillResult, FillSpec, fill_rows


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# FillSpec validation
# ---------------------------------------------------------------------------

class TestFillSpec:
    def test_valid_constant(self):
        spec = FillSpec(column="age", strategy="constant", value="0")
        assert spec.strategy == "constant"

    def test_valid_forward(self):
        spec = FillSpec(column="city", strategy="forward")
        assert spec.strategy == "forward"

    def test_valid_backward(self):
        spec = FillSpec(column="city", strategy="backward")
        assert spec.strategy == "backward"

    def test_invalid_strategy_raises(self):
        with pytest.raises(FillError, match="Unknown fill strategy"):
            FillSpec(column="x", strategy="median")


# ---------------------------------------------------------------------------
# FillResult
# ---------------------------------------------------------------------------

class TestFillResult:
    def test_defaults(self):
        r = FillResult()
        assert r.filled_count == 0
        assert r.columns_affected == []

    def test_str_shows_count_and_columns(self):
        r = FillResult(filled_count=3, columns_affected=["age", "city"])
        assert "3" in str(r)
        assert "age" in str(r)


# ---------------------------------------------------------------------------
# fill_rows — constant strategy
# ---------------------------------------------------------------------------

def test_constant_fills_empty_cells():
    rows = [_row(name="Alice", age=""), _row(name="Bob", age="30")]
    result, summary = fill_rows(rows, [FillSpec("age", "constant", "0")])
    assert result[0]["age"] == "0"
    assert result[1]["age"] == "30"
    assert summary.filled_count == 1
    assert "age" in summary.columns_affected


def test_constant_no_empty_cells_no_fill():
    rows = [_row(x="1"), _row(x="2")]
    _, summary = fill_rows(rows, [FillSpec("x", "constant", "99")])
    assert summary.filled_count == 0


# ---------------------------------------------------------------------------
# fill_rows — forward strategy
# ---------------------------------------------------------------------------

def test_forward_fill_propagates_last_value():
    rows = [
        _row(city="NYC"),
        _row(city=""),
        _row(city=""),
        _row(city="LA"),
    ]
    result, summary = fill_rows(rows, [FillSpec("city", "forward")])
    assert result[1]["city"] == "NYC"
    assert result[2]["city"] == "NYC"
    assert result[3]["city"] == "LA"
    assert summary.filled_count == 2


def test_forward_fill_leading_empty_stays_empty():
    rows = [_row(v=""), _row(v="A")]
    result, _ = fill_rows(rows, [FillSpec("v", "forward")])
    assert result[0]["v"] == ""  # nothing before it


# ---------------------------------------------------------------------------
# fill_rows — backward strategy
# ---------------------------------------------------------------------------

def test_backward_fill_uses_next_value():
    rows = [_row(score=""), _row(score=""), _row(score="10")]
    result, summary = fill_rows(rows, [FillSpec("score", "backward")])
    assert result[0]["score"] == "10"
    assert result[1]["score"] == "10"
    assert summary.filled_count == 2


# ---------------------------------------------------------------------------
# fill_rows — missing column raises
# ---------------------------------------------------------------------------

def test_missing_column_raises():
    rows = [_row(name="Alice")]
    with pytest.raises(FillError, match="not found"):
        fill_rows(rows, [FillSpec("age", "constant", "0")])


# ---------------------------------------------------------------------------
# fill_rows — empty spec list is a no-op
# ---------------------------------------------------------------------------

def test_empty_specs_returns_rows_unchanged():
    rows = [_row(a="1"), _row(a="")]
    result, summary = fill_rows(rows, [])
    assert result == rows
    assert summary.filled_count == 0
