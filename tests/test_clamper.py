"""Tests for csv_wrangler.clamper."""
from __future__ import annotations

import pytest

from csv_wrangler.clamper import (
    ClampError,
    ClampResult,
    ClampSpec,
    clamp_rows,
)


def _row(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# ClampSpec
# ---------------------------------------------------------------------------

class TestClampSpec:
    def test_valid_spec_low_only(self):
        spec = ClampSpec(column="score", low=0.0)
        assert spec.low == 0.0
        assert spec.high is None

    def test_valid_spec_high_only(self):
        spec = ClampSpec(column="score", high=100.0)
        assert spec.high == 100.0

    def test_valid_spec_both(self):
        spec = ClampSpec(column="score", low=0.0, high=100.0)
        assert spec.target == "score"

    def test_custom_dest(self):
        spec = ClampSpec(column="score", low=0.0, dest="score_clamped")
        assert spec.target == "score_clamped"

    def test_empty_column_raises(self):
        with pytest.raises(ClampError, match="column"):
            ClampSpec(column="", low=0.0)

    def test_no_bounds_raises(self):
        with pytest.raises(ClampError, match="at least one"):
            ClampSpec(column="score")

    def test_low_equals_high_raises(self):
        with pytest.raises(ClampError, match="strictly less"):
            ClampSpec(column="score", low=5.0, high=5.0)

    def test_low_greater_than_high_raises(self):
        with pytest.raises(ClampError, match="strictly less"):
            ClampSpec(column="score", low=10.0, high=5.0)


# ---------------------------------------------------------------------------
# ClampResult
# ---------------------------------------------------------------------------

class TestClampResult:
    def test_defaults(self):
        r = ClampResult()
        assert r.clamped_count == 0
        assert r.columns_affected == []

    def test_custom_values(self):
        r = ClampResult(clamped_count=3, columns_affected=["score"])
        assert r.clamped_count == 3


# ---------------------------------------------------------------------------
# clamp_rows
# ---------------------------------------------------------------------------

def _consume(rows, specs):
    it, result = clamp_rows(rows, specs)
    return list(it), result


def test_below_low_is_clamped():
    rows = [_row(score="-5")]
    spec = ClampSpec(column="score", low=0.0)
    out, result = _consume(rows, [spec])
    assert out[0]["score"] == "0"
    assert result.clamped_count == 1
    assert "score" in result.columns_affected


def test_above_high_is_clamped():
    rows = [_row(score="150")]
    spec = ClampSpec(column="score", high=100.0)
    out, result = _consume(rows, [spec])
    assert out[0]["score"] == "100"
    assert result.clamped_count == 1


def test_in_range_unchanged():
    rows = [_row(score="50")]
    spec = ClampSpec(column="score", low=0.0, high=100.0)
    out, result = _consume(rows, [spec])
    assert out[0]["score"] == "50"
    assert result.clamped_count == 0


def test_non_numeric_value_passed_through():
    rows = [_row(score="n/a")]
    spec = ClampSpec(column="score", low=0.0, high=100.0)
    out, result = _consume(rows, [spec])
    assert out[0]["score"] == "n/a"
    assert result.clamped_count == 0


def test_float_boundary_preserved():
    rows = [_row(val="3.75")]
    spec = ClampSpec(column="val", low=5.0)
    out, _ = _consume(rows, [spec])
    assert out[0]["val"] == "5"


def test_dest_column_written():
    rows = [_row(score="-1")]
    spec = ClampSpec(column="score", low=0.0, dest="score_safe")
    out, result = _consume(rows, [spec])
    assert "score_safe" in out[0]
    assert out[0]["score_safe"] == "0"
    assert "score" in out[0]  # original preserved
    assert "score_safe" in result.columns_affected


def test_missing_column_raises():
    rows = [_row(other="1")]
    spec = ClampSpec(column="score", low=0.0)
    it, _ = clamp_rows(rows, [spec])
    with pytest.raises(ClampError, match="score"):
        list(it)


def test_multiple_rows_counts_correctly():
    rows = [
        _row(score="-1"),
        _row(score="50"),
        _row(score="200"),
    ]
    spec = ClampSpec(column="score", low=0.0, high=100.0)
    out, result = _consume(rows, [spec])
    assert out[0]["score"] == "0"
    assert out[1]["score"] == "50"
    assert out[2]["score"] == "100"
    assert result.clamped_count == 2


def test_multiple_specs_independent():
    rows = [_row(a="-5", b="999")]
    specs = [
        ClampSpec(column="a", low=0.0),
        ClampSpec(column="b", high=100.0),
    ]
    out, result = _consume(rows, specs)
    assert out[0]["a"] == "0"
    assert out[0]["b"] == "100"
    assert result.clamped_count == 2
    assert sorted(result.columns_affected) == ["a", "b"]
