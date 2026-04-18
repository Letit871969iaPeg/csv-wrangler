import pytest
from csv_wrangler.deduplicator_col import (
    ColDedupeError,
    ColDedupeSpec,
    ColDedupeResult,
    dedupe_column_rows,
)


def _row(**kw):
    return dict(kw)


class TestColDedupeSpec:
    def test_valid_spec_creates_ok(self):
        s = ColDedupeSpec(column="city")
        assert s.column == "city"

    def test_empty_column_raises(self):
        with pytest.raises(ColDedupeError):
            ColDedupeSpec(column="")


class TestColDedupeResult:
    def test_defaults(self):
        r = ColDedupeResult()
        assert r.cleared_count == 0
        assert r.columns_processed == []

    def test_str_shows_counts(self):
        r = ColDedupeResult(cleared_count=3, columns_processed=["city"])
        assert "3" in str(r)
        assert "city" in str(r)

    def test_str_no_columns(self):
        r = ColDedupeResult(cleared_count=0)
        assert "none" in str(r)


class TestDedupeColumnRows:
    def test_consecutive_duplicates_cleared(self):
        rows = [
            _row(city="NYC", val="1"),
            _row(city="NYC", val="2"),
            _row(city="LA", val="3"),
        ]
        out, res = dedupe_column_rows(rows, [ColDedupeSpec("city")])
        assert out[0]["city"] == "NYC"
        assert out[1]["city"] == ""
        assert out[2]["city"] == "LA"
        assert res.cleared_count == 1

    def test_non_consecutive_not_cleared(self):
        rows = [
            _row(city="NYC"),
            _row(city="LA"),
            _row(city="NYC"),
        ]
        out, res = dedupe_column_rows(rows, [ColDedupeSpec("city")])
        assert out[2]["city"] == "NYC"
        assert res.cleared_count == 0

    def test_multiple_specs(self):
        rows = [
            _row(a="x", b="1"),
            _row(a="x", b="1"),
        ]
        out, res = dedupe_column_rows(rows, [ColDedupeSpec("a"), ColDedupeSpec("b")])
        assert out[1]["a"] == ""
        assert out[1]["b"] == ""
        assert res.cleared_count == 2

    def test_missing_column_raises(self):
        rows = [_row(x="1")]
        with pytest.raises(ColDedupeError, match="city"):
            dedupe_column_rows(rows, [ColDedupeSpec("city")])

    def test_empty_input_returns_empty(self):
        out, res = dedupe_column_rows([], [ColDedupeSpec("city")])
        assert out == []
        assert res.cleared_count == 0

    def test_columns_processed_populated(self):
        _, res = dedupe_column_rows([], [ColDedupeSpec("city"), ColDedupeSpec("name")])
        assert res.columns_processed == ["city", "name"]
