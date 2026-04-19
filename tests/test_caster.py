"""Tests for csv_wrangler.caster."""
from __future__ import annotations

import pytest
from datetime import date

from csv_wrangler.caster import CastError, CastSpec, CastResult, cast_rows


# ---------------------------------------------------------------------------
# CastSpec construction
# ---------------------------------------------------------------------------

def test_invalid_type_raises():
    with pytest.raises(CastError, match="Unknown target type"):
        CastSpec(column="x", target_type="uuid")


def test_valid_types_accepted():
    for t in ("int", "float", "bool", "date"):
        spec = CastSpec(column="x", target_type=t)
        assert spec.target_type == t


# ---------------------------------------------------------------------------
# CastSpec.cast — int
# ---------------------------------------------------------------------------

def test_cast_int_valid():
    spec = CastSpec(column="age", target_type="int")
    assert spec.cast("42") == 42


def test_cast_int_invalid_strict():
    spec = CastSpec(column="age", target_type="int", strict=True)
    with pytest.raises(CastError, match="cannot cast"):
        spec.cast("abc")


def test_cast_int_invalid_lenient():
    spec = CastSpec(column="age", target_type="int", strict=False)
    assert spec.cast("abc") == "abc"


# ---------------------------------------------------------------------------
# CastSpec.cast — float
# ---------------------------------------------------------------------------

def test_cast_float_valid():
    spec = CastSpec(column="score", target_type="float")
    assert spec.cast("3.14") == pytest.approx(3.14)


def test_cast_float_invalid_strict():
    spec = CastSpec(column="score", target_type="float", strict=True)
    with pytest.raises(CastError):
        spec.cast("n/a")


# ---------------------------------------------------------------------------
# CastSpec.cast — bool
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("val", ["1", "true", "True", "YES", "y"])
def test_cast_bool_truthy(val):
    spec = CastSpec(column="active", target_type="bool")
    assert spec.cast(val) is True


@pytest.mark.parametrize("val", ["0", "false", "False", "no", ""])
def test_cast_bool_falsy(val):
    spec = CastSpec(column="active", target_type="bool")
    assert spec.cast(val) is False


def test_cast_bool_invalid_strict():
    spec = CastSpec(column="active", target_type="bool", strict=True)
    with pytest.raises(CastError):
        spec.cast("maybe")


# ---------------------------------------------------------------------------
# CastSpec.cast — date
# ---------------------------------------------------------------------------

def test_cast_date_iso():
    spec = CastSpec(column="dob", target_type="date")
    assert spec.cast("2024-03-15") == date(2024, 3, 15)


def test_cast_date_invalid_strict():
    spec = CastSpec(column="dob", target_type="date", strict=True)
    with pytest.raises(CastError):
        spec.cast("not-a-date")


def test_cast_date_invalid_lenient():
    spec = CastSpec(column="dob", target_type="date", strict=False)
    assert spec.cast("not-a-date") == "not-a-date"


# ---------------------------------------------------------------------------
# cast_rows
# ---------------------------------------------------------------------------

def test_cast_rows_applies_specs():
    rows = [
        {"age": "30", "score": "9.5", "name": "Alice"},
        {"age": "25", "score": "8.0", "name": "Bob"},
    ]
    specs = [
        CastSpec(column="age", target_type="int"),
        CastSpec(column="score", target_type="float"),
    ]
    results = cast_rows(rows, specs)
    assert all(isinstance(r, CastResult) for r in results)
    assert results[0].row["age"] == 30
    assert results[1].row["score"] == pytest.approx(8.0)
    assert results[0].row["name"] == "Alice"
