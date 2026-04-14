"""Tests for csv_wrangler.aggregator."""
import pytest

from csv_wrangler.aggregator import (
    AggregateError,
    AggResult,
    AggSpec,
    aggregate,
)


def _rows(*dicts):
    return list(dicts)


# ---------------------------------------------------------------------------
# AggSpec validation
# ---------------------------------------------------------------------------

class TestAggSpec:
    def test_valid_ops_accepted(self):
        for op in ("sum", "mean", "min", "max", "count"):
            spec = AggSpec(column="x", op=op)
            assert spec.op == op

    def test_invalid_op_raises(self):
        with pytest.raises(AggregateError, match="Unknown aggregation op"):
            AggSpec(column="x", op="median")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# AggResult __str__
# ---------------------------------------------------------------------------

def test_str_includes_op_and_column():
    spec = AggSpec(column="price", op="sum")
    result = AggResult(spec=spec, value=42.0, row_count=3)
    s = str(result)
    assert "sum(price)" in s
    assert "42.0" in s
    assert "n=3" in s


# ---------------------------------------------------------------------------
# aggregate — count
# ---------------------------------------------------------------------------

def test_count_returns_row_count():
    rows = _rows({"}, {"a": "2"}, {"a": "3"})
    [res] = aggregate(rows, [AggSpec("a", "count")])
    assert res.value == 3.0
    assert res.row_count == 3


def test_count_empty_rows_returns_zero():
    [res] = aggregate([], [AggSpec("a", "count")])
    assert res.value == 0.0


# ---------------------------------------------------------------------------
# aggregate — numeric ops
# ---------------------------------------------------------------------------

def test_sum():
    rows = _rows({"v": "10"}, {"v": "20"}, {"v": "30"})
    [res] = aggregate(rows, [AggSpec("v", "sum")])
    assert res.value == 60.0


def test_mean():
    rows = _rows({"v": "10"}, {"v": "20"}, {"v": "30"})
    [res] = aggregate(rows, [AggSpec("v", "mean")])
    assert res.value == pytest.approx(20.0)


def test_min():
    rows = _rows({"v": "5"}, {"v": "3"}, {"v": "9"})
    [res] = aggregate(rows, [AggSpec("v", "min")])
    assert res.value == 3.0


def test_max():
    rows = _rows({"v": "5"}, {"v": "3"}, {"v": "9"})
    [res] = aggregate(rows, [AggSpec("v", "max")])
    assert res.value == 9.0


# ---------------------------------------------------------------------------
# aggregate — multiple specs
# ---------------------------------------------------------------------------

def test_multiple_specs():
    rows = _rows({"a": "1", "b": "4"}, {"a": "2", "b": "6"})
    results = aggregate(rows, [AggSpec("a", "sum"), AggSpec("b", "mean")])
    assert len(results) == 2
    assert results[0].value == 3.0
    assert results[1].value == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# aggregate — error cases
# ---------------------------------------------------------------------------

def test_missing_column_raises():
    rows = _rows({"x": "1"})
    with pytest.raises(AggregateError, match="Column 'y' not found"):
        aggregate(rows, [AggSpec("y", "sum")])


def test_non_numeric_value_raises():
    rows = _rows({"v": "abc"})
    with pytest.raises(AggregateError, match="Cannot convert"):
        aggregate(rows, [AggSpec("v", "sum")])


def test_empty_rows_numeric_op_raises():
    with pytest.raises(AggregateError, match="No rows to aggregate"):
        aggregate([], [AggSpec("v", "sum")])


def test_whitespace_values_handled():
    rows = _rows({"v": " 7 "}, {"v": "3"})
    [res] = aggregate(rows, [AggSpec("v", "sum")])
    assert res.value == 10.0
