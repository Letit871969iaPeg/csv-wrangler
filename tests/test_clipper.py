"""Tests for csv_wrangler.clipper."""
import pytest

from csv_wrangler.clipper import ClipError, ClipResult, ClipSpec, clip_rows


def _row(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# ClipSpec validation
# ---------------------------------------------------------------------------

class TestClipSpec:
    def test_valid_spec_low_only(self):
        s = ClipSpec(column="age", low=0)
        assert s.low == 0

    def test_valid_spec_high_only(self):
        s = ClipSpec(column="score", high=100)
        assert s.high == 100

    def test_valid_spec_both(self):
        s = ClipSpec(column="val", low=0, high=1)
        assert s.low == 0 and s.high == 1

    def test_neither_raises(self):
        with pytest.raises(ClipError, match="at least one"):
            ClipSpec(column="x")

    def test_inverted_range_raises(self):
        with pytest.raises(ClipError, match="must be <="):
            ClipSpec(column="x", low=10, high=5)


# ---------------------------------------------------------------------------
# ClipResult
# ---------------------------------------------------------------------------

class TestClipResult:
    def test_defaults(self):
        r = ClipResult()
        assert r.clipped_count == 0
        assert r.columns_affected == []

    def test_str_no_columns(self):
        assert "none" in str(ClipResult())

    def test_str_with_columns(self):
        r = ClipResult(clipped_count=3, columns_affected=["age"])
        assert "age" in str(r)
        assert "3" in str(r)


# ---------------------------------------------------------------------------
# clip_rows behaviour
# ---------------------------------------------------------------------------

def _consume(rows, specs, **kw):
    gen, result = clip_rows(rows, specs, **kw)
    out = list(gen)
    return out, result


def test_value_below_low_is_raised():
    rows = [_row(age="-5")]
    out, result = _consume(rows, [ClipSpec("age", low=0)])
    assert out[0]["age"] == "0"
    assert result.clipped_count == 1
    assert "age" in result.columns_affected


def test_value_above_high_is_lowered():
    rows = [_row(score="150")]
    out, result = _consume(rows, [ClipSpec("score", high=100)])
    assert out[0]["score"] == "100"
    assert result.clipped_count == 1


def test_value_within_range_unchanged():
    rows = [_row(val="50")]
    out, result = _consume(rows, [ClipSpec("val", low=0, high=100)])
    assert out[0]["val"] == "50"
    assert result.clipped_count == 0


def test_empty_string_skipped():
    rows = [_row(val="")]
    out, result = _consume(rows, [ClipSpec("val", low=0, high=10)])
    assert out[0]["val"] == ""
    assert result.clipped_count == 0


def test_non_numeric_strict_raises():
    rows = [_row(val="abc")]
    with pytest.raises(ClipError, match="Cannot convert"):
        _consume(rows, [ClipSpec("val", low=0)])


def test_non_numeric_lenient_skips():
    rows = [_row(val="abc")]
    out, result = _consume(rows, [ClipSpec("val", low=0)], strict=False)
    assert out[0]["val"] == "abc"
    assert result.clipped_count == 0


def test_missing_column_strict_raises():
    rows = [_row(other="1")]
    with pytest.raises(ClipError, match="not found"):
        _consume(rows, [ClipSpec("val", low=0)])


def test_missing_column_lenient_skips():
    rows = [_row(other="1")]
    out, result = _consume(rows, [ClipSpec("val", low=0)], strict=False)
    assert out[0] == {"other": "1"}


def test_multiple_specs_multiple_clips():
    rows = [_row(a="-1", b="200")]
    specs = [ClipSpec("a", low=0), ClipSpec("b", high=100)]
    out, result = _consume(rows, specs)
    assert out[0]["a"] == "0"
    assert out[0]["b"] == "100"
    assert result.clipped_count == 2
    assert set(result.columns_affected) == {"a", "b"}


def test_float_boundary_preserved():
    rows = [_row(val="3.7")]
    out, _ = _consume(rows, [ClipSpec("val", low=0, high=3.5)])
    assert out[0]["val"] == "3.5"
