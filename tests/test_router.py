"""Tests for csv_wrangler.router."""
from __future__ import annotations

import pytest

from csv_wrangler.router import (
    RouteError,
    RouteResult,
    RouteSpec,
    iter_bucket,
    route_rows,
)


def _row(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# RouteSpec validation
# ---------------------------------------------------------------------------

class TestRouteSpec:
    def test_valid_spec_creates_ok(self):
        spec = RouteSpec(column="status", routes={"active": "a", "inactive": "b"})
        assert spec.column == "status"

    def test_empty_column_raises(self):
        with pytest.raises(RouteError, match="column"):
            RouteSpec(column="", routes={"x": "y"})

    def test_empty_routes_raises(self):
        with pytest.raises(RouteError, match="routes"):
            RouteSpec(column="status", routes={})

    def test_empty_default_raises(self):
        with pytest.raises(RouteError, match="default"):
            RouteSpec(column="status", routes={"x": "y"}, default="")


# ---------------------------------------------------------------------------
# RouteResult helpers
# ---------------------------------------------------------------------------

class TestRouteResult:
    def test_defaults(self):
        r = RouteResult()
        assert r.total_rows == 0
        assert r.bucket_count == 0

    def test_total_rows_sums_buckets(self):
        r = RouteResult(buckets={"a": [{"x": "1"}, {"x": "2"}], "b": [{"x": "3"}]})
        assert r.total_rows == 3

    def test_bucket_count(self):
        r = RouteResult(buckets={"a": [], "b": []})
        assert r.bucket_count == 2

    def test_str_contains_bucket_names(self):
        r = RouteResult(buckets={"high": [{"v": "1"}], "low": []})
        text = str(r)
        assert "high" in text
        assert "low" in text


# ---------------------------------------------------------------------------
# route_rows
# ---------------------------------------------------------------------------

def test_routes_matching_values():
    rows = [_row(status="active"), _row(status="inactive"), _row(status="active")]
    spec = RouteSpec(column="status", routes={"active": "on", "inactive": "off"})
    result = route_rows(rows, spec)
    assert len(result.buckets["on"]) == 2
    assert len(result.buckets["off"]) == 1


def test_unmatched_rows_go_to_default():
    rows = [_row(status="pending"), _row(status="active")]
    spec = RouteSpec(column="status", routes={"active": "on"}, default="other")
    result = route_rows(rows, spec)
    assert len(result.buckets["other"]) == 1
    assert result.buckets["other"][0]["status"] == "pending"


def test_missing_column_raises():
    rows = [_row(name="Alice")]
    spec = RouteSpec(column="status", routes={"active": "on"})
    with pytest.raises(RouteError, match="status"):
        route_rows(rows, spec)


def test_empty_input_returns_empty_result():
    spec = RouteSpec(column="status", routes={"active": "on"})
    result = route_rows([], spec)
    assert result.total_rows == 0
    assert result.bucket_count == 0


def test_rows_are_copies():
    original = _row(status="active", name="Alice")
    spec = RouteSpec(column="status", routes={"active": "on"})
    result = route_rows([original], spec)
    result.buckets["on"][0]["name"] = "MUTATED"
    assert original["name"] == "Alice"


# ---------------------------------------------------------------------------
# iter_bucket
# ---------------------------------------------------------------------------

def test_iter_bucket_yields_rows():
    rows = [_row(t="x"), _row(t="x"), _row(t="y")]
    spec = RouteSpec(column="t", routes={"x": "ex", "y": "why"})
    result = route_rows(rows, spec)
    ex_rows = list(iter_bucket(result, "ex"))
    assert len(ex_rows) == 2


def test_iter_bucket_missing_label_yields_nothing():
    result = RouteResult(buckets={"a": [{"x": "1"}]})
    assert list(iter_bucket(result, "nonexistent")) == []
