"""Tests for csv_wrangler.counter."""
from __future__ import annotations

import pytest

from csv_wrangler.counter import (
    CountError,
    CountResult,
    CountSpec,
    count_rows,
    _iter,
)


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# CountSpec
# ---------------------------------------------------------------------------

class TestCountSpec:
    def test_valid_spec_creates_ok(self):
        spec = CountSpec(column="city")
        assert spec.column == "city"

    def test_dest_column_defaults_to_column_count(self):
        spec = CountSpec(column="city")
        assert spec.dest_column == "city_count"

    def test_custom_dest_column(self):
        spec = CountSpec(column="city", dest_column="freq")
        assert spec.dest_column == "freq"

    def test_empty_column_raises(self):
        with pytest.raises(CountError, match="column"):
            CountSpec(column="")

    def test_invalid_sort_raises(self):
        with pytest.raises(CountError, match="sort"):
            CountSpec(column="city", sort="random")

    def test_valid_sort_values(self):
        for s in ("asc", "desc", "none"):
            spec = CountSpec(column="x", sort=s)
            assert spec.sort == s


# ---------------------------------------------------------------------------
# CountResult
# ---------------------------------------------------------------------------

class TestCountResult:
    def test_defaults(self):
        spec = CountSpec(column="city")
        result = CountResult(spec=spec)
        assert result.rows == []
        assert result.total_rows == 0

    def test_str_shows_column_and_counts(self):
        spec = CountSpec(column="city")
        result = CountResult(spec=spec, rows=[{"city": "NYC", "city_count": "3"}], total_rows=5)
        s = str(result)
        assert "city" in s
        assert "unique=1" in s
        assert "total_input=5" in s


# ---------------------------------------------------------------------------
# count_rows
# ---------------------------------------------------------------------------

def test_basic_count():
    rows = [
        _row(city="NYC"),
        _row(city="LA"),
        _row(city="NYC"),
        _row(city="NYC"),
        _row(city="LA"),
    ]
    result = count_rows(rows, CountSpec(column="city"))
    assert result.total_rows == 5
    counts = {r["city"]: int(r["city_count"]) for r in result.rows}
    assert counts["NYC"] == 3
    assert counts["LA"] == 2


def test_sort_desc_order():
    rows = [_row(x="a"), _row(x="b"), _row(x="a"), _row(x="c"), _row(x="a")]
    result = count_rows(rows, CountSpec(column="x", sort="desc"))
    values = [r["x"] for r in result.rows]
    assert values[0] == "a"  # highest count first


def test_sort_asc_order():
    rows = [_row(x="a"), _row(x="b"), _row(x="a"), _row(x="c"), _row(x="a")]
    result = count_rows(rows, CountSpec(column="x", sort="asc"))
    values = [r["x"] for r in result.rows]
    assert values[-1] == "a"  # highest count last


def test_sort_none_preserves_insertion_order():
    rows = [_row(x="b"), _row(x="a"), _row(x="b")]
    result = count_rows(rows, CountSpec(column="x", sort="none"))
    values = [r["x"] for r in result.rows]
    # Counter insertion order: b first, then a
    assert values[0] == "b"


def test_missing_column_raises():
    rows = [_row(city="NYC")]
    with pytest.raises(CountError, match="not found"):
        count_rows(rows, CountSpec(column="missing"))


def test_empty_input_returns_zero_total():
    result = count_rows([], CountSpec(column="city"))
    assert result.total_rows == 0
    assert result.rows == []


def test_iter_yields_rows():
    rows = [_row(city="NYC"), _row(city="NYC"), _row(city="LA")]
    result = count_rows(rows, CountSpec(column="city"))
    output = list(_iter(result))
    assert len(output) == 2
