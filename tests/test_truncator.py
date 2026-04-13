"""Tests for csv_wrangler.truncator."""
from __future__ import annotations

import pytest

from csv_wrangler.truncator import TruncateError, TruncateResult, truncate_rows


def _rows(*dicts: dict[str, str]) -> list[dict[str, str]]:
    return list(dicts)


# ---------------------------------------------------------------------------
# TruncateResult helpers
# ---------------------------------------------------------------------------

class TestTruncateResult:
    def test_was_lossy_false_when_no_truncations(self):
        r = TruncateResult(total_rows=5, truncated_cells=0)
        assert r.was_lossy is False

    def test_was_lossy_true_when_truncations_exist(self):
        r = TruncateResult(total_rows=5, truncated_cells=2)
        assert r.was_lossy is True

    def test_columns_affected_default_empty(self):
        r = TruncateResult()
        assert r.columns_affected == set()


# ---------------------------------------------------------------------------
# truncate_rows – validation
# ---------------------------------------------------------------------------

def test_max_length_zero_raises():
    with pytest.raises(TruncateError, match="max_length"):
        truncate_rows([], max_length=0)


def test_max_length_negative_raises():
    with pytest.raises(TruncateError, match="max_length"):
        truncate_rows([], max_length=-3)


def test_ellipsis_too_long_raises():
    with pytest.raises(TruncateError, match="ellipsis_str"):
        truncate_rows([], max_length=3, ellipsis_str="...")


# ---------------------------------------------------------------------------
# truncate_rows – happy paths
# ---------------------------------------------------------------------------

def test_short_values_unchanged():
    rows = _rows({"name": "Al", "city": "NY"})
    it, result = truncate_rows(rows, max_length=10)
    output = list(it)
    assert output == [{"name": "Al", "city": "NY"}]
    assert result.truncated_cells == 0
    assert result.was_lossy is False


def test_long_value_truncated_with_ellipsis():
    rows = _rows({"bio": "Hello, World!"})
    it, result = truncate_rows(rows, max_length=8, ellipsis_str="...")
    output = list(it)
    assert output[0]["bio"] == "Hello..."
    assert result.truncated_cells == 1
    assert "bio" in result.columns_affected


def test_total_rows_counted():
    rows = _rows({"x": "a"}, {"x": "b"}, {"x": "c"})
    it, result = truncate_rows(rows, max_length=5)
    list(it)
    assert result.total_rows == 3


def test_multiple_cells_truncated():
    rows = _rows({"a": "toolong", "b": "alsotoolong"})
    it, result = truncate_rows(rows, max_length=5, ellipsis_str=".")
    output = list(it)
    assert output[0]["a"] == "tool."
    assert output[0]["b"] == "also."
    assert result.truncated_cells == 2
    assert result.columns_affected == {"a", "b"}


def test_column_filter_restricts_truncation():
    rows = _rows({"name": "Alexander", "code": "ABCDEFGH"})
    it, result = truncate_rows(rows, max_length=5, columns=["name"], ellipsis_str="..")
    output = list(it)
    assert output[0]["name"] == "Ale.."
    assert output[0]["code"] == "ABCDEFGH"  # untouched
    assert result.truncated_cells == 1
    assert result.columns_affected == {"name"}


def test_empty_input():
    it, result = truncate_rows([], max_length=5)
    assert list(it) == []
    assert result.total_rows == 0
    assert result.truncated_cells == 0


def test_custom_ellipsis():
    rows = _rows({"val": "abcdef"})
    it, result = truncate_rows(rows, max_length=4, ellipsis_str="~")
    output = list(it)
    assert output[0]["val"] == "abc~"
