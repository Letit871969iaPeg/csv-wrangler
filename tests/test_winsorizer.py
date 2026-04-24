"""Tests for csv_wrangler.winsorizer."""
import pytest
from csv_wrangler.winsorizer import (
    WinsorizeError,
    WinsorizeSpec,
    WinsorizeResult,
    winsorize_rows,
)


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# WinsorizeSpec validation
# ---------------------------------------------------------------------------

class TestWinsorizeSpec:
    def test_valid_spec_creates_ok(self):
        spec = WinsorizeSpec(column="score", lower=0.05, upper=0.95)
        assert spec.column == "score"

    def test_empty_column_raises(self):
        with pytest.raises(WinsorizeError, match="column"):
            WinsorizeSpec(column="")

    def test_lower_equals_upper_raises(self):
        with pytest.raises(WinsorizeError):
            WinsorizeSpec(column="x", lower=0.5, upper=0.5)

    def test_lower_greater_than_upper_raises(self):
        with pytest.raises(WinsorizeError):
            WinsorizeSpec(column="x", lower=0.9, upper=0.1)

    def test_lower_negative_raises(self):
        with pytest.raises(WinsorizeError):
            WinsorizeSpec(column="x", lower=-0.1, upper=0.9)

    def test_upper_above_one_raises(self):
        with pytest.raises(WinsorizeError):
            WinsorizeSpec(column="x", lower=0.05, upper=1.1)


# ---------------------------------------------------------------------------
# WinsorizeResult
# ---------------------------------------------------------------------------

class TestWinsorizeResult:
    def test_defaults(self):
        r = WinsorizeResult()
        assert r.clamped_low == 0
        assert r.clamped_high == 0
        assert r.columns_affected == []

    def test_str_no_columns(self):
        r = WinsorizeResult()
        assert "none" in str(r)

    def test_str_with_columns(self):
        r = WinsorizeResult(clamped_low=2, clamped_high=1, columns_affected=["score"])
        assert "score" in str(r)
        assert "2" in str(r)


# ---------------------------------------------------------------------------
# winsorize_rows
# ---------------------------------------------------------------------------

def test_empty_rows_returns_empty():
    rows, result = winsorize_rows([], [WinsorizeSpec("score")])
    assert rows == []
    assert result.clamped_low == 0


def test_no_specs_returns_rows_unchanged():
    data = [_row(score="10"), _row(score="20")]
    rows, result = winsorize_rows(data, [])
    assert len(rows) == 2
    assert result.columns_affected == []


def test_clamps_low_outliers():
    data = [_row(score=str(v)) for v in [1, 50, 50, 50, 50, 50, 50, 50, 50, 100]]
    spec = WinsorizeSpec(column="score", lower=0.1, upper=0.9)
    rows, result = winsorize_rows(data, [spec])
    assert result.clamped_low >= 1
    assert "score" in result.columns_affected


def test_clamps_high_outliers():
    data = [_row(score=str(v)) for v in [1, 2, 3, 4, 5, 6, 7, 8, 9, 1000]]
    spec = WinsorizeSpec(column="score", lower=0.05, upper=0.9)
    rows, result = winsorize_rows(data, [spec])
    assert result.clamped_high >= 1


def test_non_numeric_values_skipped():
    data = [_row(score="abc"), _row(score="50"), _row(score="xyz")]
    spec = WinsorizeSpec(column="score", lower=0.1, upper=0.9)
    rows, result = winsorize_rows(data, [spec])
    assert rows[0]["score"] == "abc"  # untouched


def test_missing_column_no_error():
    data = [_row(name="Alice"), _row(name="Bob")]
    spec = WinsorizeSpec(column="score")
    rows, result = winsorize_rows(data, [spec])
    assert result.columns_affected == []


def test_multiple_specs_tracked_independently():
    data = [
        _row(a=str(v), b=str(v * 2))
        for v in [1, 5, 5, 5, 5, 5, 5, 5, 5, 100]
    ]
    specs = [
        WinsorizeSpec(column="a", lower=0.1, upper=0.9),
        WinsorizeSpec(column="b", lower=0.1, upper=0.9),
    ]
    _, result = winsorize_rows(data, specs)
    assert len(result.columns_affected) == 2
