"""Tests for csv_wrangler.highlighter."""
from __future__ import annotations

import pytest

from csv_wrangler.highlighter import (
    HighlightError,
    HighlightResult,
    HighlightSpec,
    highlight_rows,
)


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# HighlightSpec validation
# ---------------------------------------------------------------------------

class TestHighlightSpec:
    def test_valid_spec_creates_ok(self):
        spec = HighlightSpec(column="name", pattern="Alice")
        assert spec.column == "name"
        assert spec.dest == "_highlighted"

    def test_empty_column_raises(self):
        with pytest.raises(HighlightError, match="column"):
            HighlightSpec(column="", pattern="x")

    def test_empty_pattern_raises(self):
        with pytest.raises(HighlightError, match="pattern"):
            HighlightSpec(column="name", pattern="")

    def test_empty_dest_raises(self):
        with pytest.raises(HighlightError, match="dest"):
            HighlightSpec(column="name", pattern="x", dest="")

    def test_custom_dest(self):
        spec = HighlightSpec(column="city", pattern="NY", dest="is_ny")
        assert spec.dest == "is_ny"


# ---------------------------------------------------------------------------
# HighlightResult
# ---------------------------------------------------------------------------

class TestHighlightResult:
    def test_defaults(self):
        r = HighlightResult()
        assert r.highlighted_count == 0
        assert r.total_rows == 0
        assert r.specs == []

    def test_str_shows_counts(self):
        spec = HighlightSpec(column="name", pattern="Alice")
        r = HighlightResult(highlighted_count=2, total_rows=5, specs=[spec])
        s = str(r)
        assert "2/5" in s
        assert "1 spec" in s


# ---------------------------------------------------------------------------
# highlight_rows
# ---------------------------------------------------------------------------

def test_no_specs_raises():
    with pytest.raises(HighlightError, match="at least one"):
        it, _ = highlight_rows([], [])
        list(it)


def test_basic_match():
    rows = [_row(name="Alice", city="NY"), _row(name="Bob", city="LA")]
    spec = HighlightSpec(column="name", pattern="Alice", dest="flag")
    it, result = highlight_rows(rows, [spec])
    out = list(it)
    assert out[0]["flag"] == "1"
    assert out[1]["flag"] == "0"
    assert result.highlighted_count == 1
    assert result.total_rows == 2


def test_no_match_value_applied():
    rows = [_row(name="Carol")]
    spec = HighlightSpec(column="name", pattern="Alice", match_value="yes", no_match_value="no")
    it, _ = highlight_rows(rows, [spec])
    out = list(it)
    assert out[0]["_highlighted"] == "no"


def test_case_insensitive_match():
    rows = [_row(name="alice")]
    spec = HighlightSpec(column="name", pattern="Alice", case_sensitive=False)
    it, result = highlight_rows(rows, [spec])
    out = list(it)
    assert out[0]["_highlighted"] == "1"
    assert result.highlighted_count == 1


def test_case_sensitive_no_match():
    rows = [_row(name="alice")]
    spec = HighlightSpec(column="name", pattern="Alice", case_sensitive=True)
    it, result = highlight_rows(rows, [spec])
    out = list(it)
    assert out[0]["_highlighted"] == "0"
    assert result.highlighted_count == 0


def test_missing_column_raises():
    rows = [_row(city="NY")]
    spec = HighlightSpec(column="name", pattern="Alice")
    it, _ = highlight_rows(rows, [spec])
    with pytest.raises(HighlightError, match="name"):
        list(it)


def test_multiple_specs_independent_dest():
    rows = [_row(name="Alice", city="New York")]
    specs = [
        HighlightSpec(column="name", pattern="Alice", dest="name_flag"),
        HighlightSpec(column="city", pattern="York", dest="city_flag"),
    ]
    it, result = highlight_rows(rows, specs)
    out = list(it)
    assert out[0]["name_flag"] == "1"
    assert out[0]["city_flag"] == "1"
    assert result.highlighted_count == 1


def test_highlighted_count_counts_rows_not_specs():
    rows = [
        _row(name="Alice", city="NY"),
        _row(name="Alice", city="LA"),
        _row(name="Bob", city="NY"),
    ]
    specs = [
        HighlightSpec(column="name", pattern="Alice", dest="name_flag"),
        HighlightSpec(column="city", pattern="NY", dest="city_flag"),
    ]
    it, result = highlight_rows(rows, specs)
    list(it)
    # All three rows have at least one match
    assert result.highlighted_count == 3
