"""Tests for csv_wrangler.condenser."""
import pytest
from csv_wrangler.condenser import (
    CondenserError,
    CondenserSpec,
    CondenserResult,
    condense_rows,
)


def _row(**kw: str) -> dict[str, str]:
    return dict(kw)


class TestCondenserSpec:
    def test_valid_spec_creates_ok(self):
        s = CondenserSpec(columns=["a", "b"], dest="ab")
        assert s.dest == "ab"

    def test_empty_columns_raises(self):
        with pytest.raises(CondenserError, match="columns"):
            CondenserSpec(columns=[], dest="x")

    def test_single_column_raises(self):
        with pytest.raises(CondenserError, match="two source"):
            CondenserSpec(columns=["a"], dest="x")

    def test_empty_dest_raises(self):
        with pytest.raises(CondenserError, match="dest"):
            CondenserSpec(columns=["a", "b"], dest="")


class TestCondenserResult:
    def test_defaults(self):
        r = CondenserResult()
        assert r.condensed_count == 0
        assert r.skipped_rows == 0

    def test_str(self):
        r = CondenserResult(condensed_count=3, skipped_rows=1)
        assert "3" in str(r)
        assert "1" in str(r)


class TestCondenseRows:
    def test_basic_condense(self):
        rows = [_row(first="John", last="Doe", age="30")]
        spec = CondenserSpec(columns=["first", "last"], dest="full_name")
        out, result = condense_rows(rows, spec)
        assert out[0]["full_name"] == "John Doe"
        assert result.condensed_count == 1

    def test_drops_source_columns_by_default(self):
        rows = [_row(first="Jane", last="Smith")]
        spec = CondenserSpec(columns=["first", "last"], dest="full")
        out, _ = condense_rows(rows, spec)
        assert "first" not in out[0]
        assert "last" not in out[0]

    def test_keeps_source_columns_when_drop_false(self):
        rows = [_row(first="Jane", last="Smith")]
        spec = CondenserSpec(columns=["first", "last"], dest="full", drop_sources=False)
        out, _ = condense_rows(rows, spec)
        assert "first" in out[0]
        assert "last" in out[0]
        assert out[0]["full"] == "Jane Smith"

    def test_custom_delimiter(self):
        rows = [_row(city="NYC", state="NY")]
        spec = CondenserSpec(columns=["city", "state"], dest="location", delimiter=", ")
        out, _ = condense_rows(rows, spec)
        assert out[0]["location"] == "NYC, NY"

    def test_missing_column_skips_row(self):
        rows = [_row(first="Only")]
        spec = CondenserSpec(columns=["first", "last"], dest="full")
        out, result = condense_rows(rows, spec)
        assert result.skipped_rows == 1
        assert result.condensed_count == 0
        assert out[0] == {"first": "Only"}

    def test_three_columns(self):
        rows = [_row(a="x", b="y", c="z")]
        spec = CondenserSpec(columns=["a", "b", "c"], dest="abc", delimiter="-")
        out, _ = condense_rows(rows, spec)
        assert out[0]["abc"] == "x-y-z"

    def test_empty_input(self):
        out, result = condense_rows([], CondenserSpec(columns=["a", "b"], dest="ab"))
        assert out == []
        assert result.condensed_count == 0
