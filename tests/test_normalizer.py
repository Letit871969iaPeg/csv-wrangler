"""Tests for csv_wrangler.normalizer."""
import pytest

from csv_wrangler.normalizer import (
    NormalizeError,
    NormalizeResult,
    NormalizeSpec,
    normalize_rows,
)


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# NormalizeSpec
# ---------------------------------------------------------------------------

class TestNormalizeSpec:
    def test_valid_modes_accepted(self):
        for mode in ("strip", "lower", "upper", "title"):
            spec = NormalizeSpec(column="x", mode=mode)
            assert spec.mode == mode

    def test_invalid_mode_raises(self):
        with pytest.raises(NormalizeError, match="Invalid mode"):
            NormalizeSpec(column="x", mode="camel")


# ---------------------------------------------------------------------------
# normalize_rows — mode behaviour
# ---------------------------------------------------------------------------

def test_strip_removes_whitespace():
    rows = [_row(name="  Alice  ", city="NYC")]
    specs = [NormalizeSpec(column="name", mode="strip")]
    it, result = normalize_rows(rows, specs)
    out = list(it)
    assert out[0]["name"] == "Alice"
    assert result.normalized_count == 1


def test_lower_lowercases_value():
    rows = [_row(name="ALICE")]
    specs = [NormalizeSpec(column="name", mode="lower")]
    it, _ = normalize_rows(rows, specs)
    assert list(it)[0]["name"] == "alice"


def test_upper_uppercases_value():
    rows = [_row(name="alice")]
    specs = [NormalizeSpec(column="name", mode="upper")]
    it, _ = normalize_rows(rows, specs)
    assert list(it)[0]["name"] == "ALICE"


def test_title_titlecases_value():
    rows = [_row(name="alice smith")]
    specs = [NormalizeSpec(column="name", mode="title")]
    it, _ = normalize_rows(rows, specs)
    assert list(it)[0]["name"] == "Alice Smith"


def test_untouched_columns_unchanged():
    rows = [_row(name="  Alice  ", city="new york")]
    specs = [NormalizeSpec(column="name", mode="strip")]
    it, _ = normalize_rows(rows, specs)
    assert list(it)[0]["city"] == "new york"


def test_multiple_specs_applied():
    rows = [_row(name="  alice  ", city="new york")]
    specs = [
        NormalizeSpec(column="name", mode="strip"),
        NormalizeSpec(column="city", mode="title"),
    ]
    it, result = normalize_rows(rows, specs)
    out = list(it)[0]
    assert out["name"] == "alice"
    assert out["city"] == "New York"
    assert result.normalized_count == 2


def test_missing_column_recorded_in_skipped():
    rows = [_row(name="alice")]
    specs = [NormalizeSpec(column="ghost", mode="lower")]
    it, result = normalize_rows(rows, specs)
    list(it)  # exhaust iterator
    assert "ghost" in result.skipped_columns
    assert result.normalized_count == 0


def test_empty_rows_returns_empty_iterator():
    it, result = normalize_rows([], [NormalizeSpec(column="name", mode="lower")])
    assert list(it) == []
    assert result.normalized_count == 0


def test_normalize_result_str_no_skipped():
    r = NormalizeResult(normalized_count=3)
    assert "normalized=3" in str(r)
    assert "skipped" not in str(r)


def test_normalize_result_str_with_skipped():
    r = NormalizeResult(normalized_count=1, skipped_columns=["ghost"])
    assert "skipped" in str(r)
