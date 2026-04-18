"""Tests for csv_wrangler.splitter_col."""
import pytest
from csv_wrangler.splitter_col import (
    ColSplitError,
    ColSplitSpec,
    ColSplitResult,
    split_column,
    _iter,
)


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


class TestColSplitSpec:
    def test_valid_spec_creates_ok(self):
        s = ColSplitSpec(column="name", delimiter=" ", into=["first", "last"])
        assert s.column == "name"

    def test_empty_column_raises(self):
        with pytest.raises(ColSplitError):
            ColSplitSpec(column="", delimiter=" ", into=["a", "b"])

    def test_empty_delimiter_raises(self):
        with pytest.raises(ColSplitError):
            ColSplitSpec(column="name", delimiter="", into=["a", "b"])

    def test_single_into_raises(self):
        with pytest.raises(ColSplitError):
            ColSplitSpec(column="name", delimiter=" ", into=["only"])


class TestColSplitResult:
    def test_defaults(self):
        r = ColSplitResult()
        assert r.rows_processed == 0
        assert r.rows_split == 0
        assert r.columns_added == []

    def test_str_shows_counts(self):
        r = ColSplitResult(rows_processed=3, rows_split=2, columns_added=["a", "b"])
        assert "3" in str(r)
        assert "2" in str(r)


class TestSplitColumn:
    def test_basic_split(self):
        rows = [_row(name="John Doe", age="30")]
        spec = ColSplitSpec(column="name", delimiter=" ", into=["first", "last"])
        out, result = split_column(rows, spec)
        assert out[0]["first"] == "John"
        assert out[0]["last"] == "Doe"

    def test_source_dropped_by_default(self):
        rows = [_row(name="John Doe")]
        spec = ColSplitSpec(column="name", delimiter=" ", into=["first", "last"])
        out, _ = split_column(rows, spec)
        assert "name" not in out[0]

    def test_source_kept_when_requested(self):
        rows = [_row(name="John Doe")]
        spec = ColSplitSpec(column="name", delimiter=" ", into=["first", "last"], drop_source=False)
        out, _ = split_column(rows, spec)
        assert "name" in out[0]

    def test_missing_column_raises(self):
        rows = [_row(age="30")]
        spec = ColSplitSpec(column="name", delimiter=" ", into=["first", "last"])
        with pytest.raises(ColSplitError):
            split_column(rows, spec)

    def test_fewer_parts_than_targets_fills_empty(self):
        rows = [_row(name="John")]
        spec = ColSplitSpec(column="name", delimiter=" ", into=["first", "last"])
        out, _ = split_column(rows, spec)
        assert out[0]["first"] == "John"
        assert out[0]["last"] == ""

    def test_result_counts(self):
        rows = [_row(name="A B"), _row(name="C D")]
        spec = ColSplitSpec(column="name", delimiter=" ", into=["first", "last"])
        _, result = split_column(rows, spec)
        assert result.rows_processed == 2
        assert result.rows_split == 2
        assert result.columns_added == ["first", "last"]

    def test_comma_delimiter(self):
        rows = [_row(tags="a,b,c")]
        spec = ColSplitSpec(column="tags", delimiter=",", into=["t1", "t2", "t3"])
        out, _ = split_column(rows, spec)
        assert out[0]["t1"] == "a"
        assert out[0]["t2"] == "b"
        assert out[0]["t3"] == "c"

    def test_iter_yields_correct_rows(self):
        rows = [_row(name="X Y"), _row(name="P Q")]
        spec = ColSplitSpec(column="name", delimiter=" ", into=["first", "last"])
        out = list(_iter(rows, spec))
        assert len(out) == 2
        assert out[1]["last"] == "Q"
