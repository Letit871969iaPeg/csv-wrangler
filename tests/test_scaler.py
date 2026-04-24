"""Tests for csv_wrangler.scaler."""
import pytest
from csv_wrangler.scaler import ScaleError, ScaleSpec, ScaleResult, scale_rows


def _row(**kw: str) -> dict[str, str]:
    return dict(kw)


# ---------------------------------------------------------------------------
# ScaleSpec validation
# ---------------------------------------------------------------------------

class TestScaleSpec:
    def test_valid_minmax(self):
        s = ScaleSpec(column="score", method="minmax")
        assert s.dest == "score"

    def test_valid_zscore_with_dest(self):
        s = ScaleSpec(column="score", method="zscore", dest="score_z")
        assert s.dest == "score_z"

    def test_empty_column_raises(self):
        with pytest.raises(ScaleError, match="column"):
            ScaleSpec(column="", method="minmax")

    def test_invalid_method_raises(self):
        with pytest.raises(ScaleError, match="unknown method"):
            ScaleSpec(column="score", method="log")

    def test_dest_defaults_to_column(self):
        s = ScaleSpec(column="val", method="zscore")
        assert s.dest == "val"


# ---------------------------------------------------------------------------
# ScaleResult
# ---------------------------------------------------------------------------

class TestScaleResult:
    def test_defaults(self):
        r = ScaleResult()
        assert r.columns_scaled == []
        assert r.rows_processed == 0
        assert r.skipped_non_numeric == 0

    def test_str_shows_counts(self):
        r = ScaleResult(columns_scaled=["a"], rows_processed=10, skipped_non_numeric=2)
        s = str(r)
        assert "1 column" in s
        assert "10 row" in s
        assert "2 non-numeric" in s


# ---------------------------------------------------------------------------
# scale_rows — minmax
# ---------------------------------------------------------------------------

def test_minmax_zero_to_one():
    rows = [_row(v="0"), _row(v="5"), _row(v="10")]
    out, result = scale_rows(rows, [ScaleSpec(column="v", method="minmax")])
    assert float(out[0]["v"]) == pytest.approx(0.0)
    assert float(out[1]["v"]) == pytest.approx(0.5)
    assert float(out[2]["v"]) == pytest.approx(1.0)
    assert result.rows_processed == 3


def test_minmax_constant_column_yields_zero():
    rows = [_row(v="7"), _row(v="7"), _row(v="7")]
    out, _ = scale_rows(rows, [ScaleSpec(column="v", method="minmax")])
    assert all(float(r["v"]) == 0.0 for r in out)


# ---------------------------------------------------------------------------
# scale_rows — zscore
# ---------------------------------------------------------------------------

def test_zscore_mean_is_zero():
    rows = [_row(v="2"), _row(v="4"), _row(v="6")]
    out, _ = scale_rows(rows, [ScaleSpec(column="v", method="zscore")])
    mean = sum(float(r["v"]) for r in out) / len(out)
    assert mean == pytest.approx(0.0, abs=1e-9)


def test_zscore_constant_column_yields_zero():
    rows = [_row(v="3"), _row(v="3")]
    out, _ = scale_rows(rows, [ScaleSpec(column="v", method="zscore")])
    assert all(float(r["v"]) == 0.0 for r in out)


# ---------------------------------------------------------------------------
# Non-numeric handling
# ---------------------------------------------------------------------------

def test_non_numeric_values_left_unchanged():
    rows = [_row(v="hello"), _row(v="1"), _row(v="2")]
    out, result = scale_rows(rows, [ScaleSpec(column="v", method="minmax")])
    assert out[0]["v"] == "hello"
    assert result.skipped_non_numeric == 1


# ---------------------------------------------------------------------------
# dest column
# ---------------------------------------------------------------------------

def test_dest_column_written_separately():
    rows = [_row(score="0"), _row(score="10")]
    out, _ = scale_rows(rows, [ScaleSpec(column="score", method="minmax", dest="score_norm")])
    assert "score_norm" in out[0]
    assert out[0]["score"] == "0"  # original preserved


def test_empty_rows_returns_empty():
    out, result = scale_rows([], [ScaleSpec(column="v", method="minmax")])
    assert out == []
    assert result.rows_processed == 0
