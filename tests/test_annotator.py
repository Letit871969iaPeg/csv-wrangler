"""Tests for csv_wrangler.annotator."""

from __future__ import annotations

import pytest

from csv_wrangler.annotator import (
    AnnotateError,
    AnnotateResult,
    AnnotateSpec,
    annotate_rows,
)


def _row(**kwargs: str) -> dict:
    return dict(kwargs)


def _consume(iterator):
    return list(iterator)


# ---------------------------------------------------------------------------
# AnnotateSpec validation
# ---------------------------------------------------------------------------

class TestAnnotateSpec:
    def test_valid_spec_creates_ok(self):
        spec = AnnotateSpec(column="upper_name", expression=lambda r: r["name"].upper())
        assert spec.column == "upper_name"

    def test_empty_column_raises(self):
        with pytest.raises(AnnotateError, match="column name"):
            AnnotateSpec(column="", expression=lambda r: "")

    def test_non_callable_expression_raises(self):
        with pytest.raises(AnnotateError, match="callable"):
            AnnotateSpec(column="x", expression="not_a_function")  # type: ignore


# ---------------------------------------------------------------------------
# annotate_rows
# ---------------------------------------------------------------------------

class TestAnnotateRows:
    def test_adds_new_column(self):
        rows = [_row(name="alice"), _row(name="bob")]
        spec = AnnotateSpec(column="upper", expression=lambda r: r["name"].upper())
        it, result = annotate_rows(rows, [spec])
        out = _consume(it)
        assert out[0]["upper"] == "ALICE"
        assert out[1]["upper"] == "BOB"

    def test_result_tracks_added_column(self):
        rows = [_row(name="alice")]
        spec = AnnotateSpec(column="upper", expression=lambda r: r["name"].upper())
        it, result = annotate_rows(rows, [spec])
        _consume(it)
        assert "upper" in result.added_columns

    def test_result_row_count(self):
        rows = [_row(x="1"), _row(x="2"), _row(x="3")]
        spec = AnnotateSpec(column="y", expression=lambda r: r["x"])
        it, result = annotate_rows(rows, [spec])
        _consume(it)
        assert result.row_count == 3

    def test_existing_column_without_overwrite_raises(self):
        rows = [_row(name="alice", upper="X")]
        spec = AnnotateSpec(column="upper", expression=lambda r: r["name"].upper())
        it, _ = annotate_rows(rows, [spec])
        with pytest.raises(AnnotateError, match="already exists"):
            _consume(it)

    def test_existing_column_with_overwrite_ok(self):
        rows = [_row(name="alice", upper="X")]
        spec = AnnotateSpec(
            column="upper",
            expression=lambda r: r["name"].upper(),
            overwrite=True,
        )
        it, result = annotate_rows(rows, [spec])
        out = _consume(it)
        assert out[0]["upper"] == "ALICE"
        assert "upper" in result.overwritten_columns

    def test_expression_error_raises_annotate_error(self):
        rows = [_row(val="abc")]
        spec = AnnotateSpec(column="num", expression=lambda r: str(int(r["val"])))
        it, _ = annotate_rows(rows, [spec])
        with pytest.raises(AnnotateError, match="failed on row"):
            _consume(it)

    def test_multiple_specs_applied(self):
        rows = [_row(a="1", b="2")]
        specs = [
            AnnotateSpec(column="sum", expression=lambda r: str(int(r["a"]) + int(r["b"]))),
            AnnotateSpec(column="tag", expression=lambda r: "ok"),
        ]
        it, result = annotate_rows(rows, specs)
        out = _consume(it)
        assert out[0]["sum"] == "3"
        assert out[0]["tag"] == "ok"
        assert len(result.added_columns) == 2

    def test_empty_input_yields_nothing(self):
        it, result = annotate_rows([], [])
        assert _consume(it) == []
        assert result.row_count == 0

    def test_str_representation(self):
        r = AnnotateResult(added_columns=["x"], overwritten_columns=[], row_count=5)
        assert "rows=5" in str(r)
        assert "added=[x]" in str(r)
