"""Tests for csv_wrangler/masker.py"""
import pytest
from csv_wrangler.masker import (
    MaskError,
    MaskSpec,
    MaskResult,
    mask_rows,
    _mask_value,
)


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# MaskSpec validation
# ---------------------------------------------------------------------------

class TestMaskSpec:
    def test_valid_spec_creates_ok(self):
        spec = MaskSpec(column="email", mode="full", char="*", keep=4)
        assert spec.column == "email"

    def test_invalid_mode_raises(self):
        with pytest.raises(MaskError, match="Invalid mode"):
            MaskSpec(column="x", mode="scramble")

    def test_multi_char_fill_raises(self):
        with pytest.raises(MaskError, match="one character"):
            MaskSpec(column="x", char="**")

    def test_negative_keep_raises(self):
        with pytest.raises(MaskError, match="keep must be"):
            MaskSpec(column="x", keep=-1)


# ---------------------------------------------------------------------------
# _mask_value
# ---------------------------------------------------------------------------

class TestMaskValue:
    def test_full_replaces_all(self):
        spec = MaskSpec(column="c", mode="full")
        assert _mask_value("hello", spec) == "*****"

    def test_partial_keeps_last_n(self):
        spec = MaskSpec(column="c", mode="partial", keep=4)
        assert _mask_value("1234567890", spec) == "******7890"

    def test_first_keeps_first_n(self):
        spec = MaskSpec(column="c", mode="first", keep=3)
        assert _mask_value("abcdef", spec) == "abc***"

    def test_last_keeps_last_n(self):
        spec = MaskSpec(column="c", mode="last", keep=2)
        assert _mask_value("abcdef", spec) == "****ef"

    def test_empty_value_unchanged(self):
        spec = MaskSpec(column="c", mode="full")
        assert _mask_value("", spec) == ""

    def test_keep_larger_than_value_clamps(self):
        spec = MaskSpec(column="c", mode="partial", keep=100)
        assert _mask_value("abc", spec) == "abc"


# ---------------------------------------------------------------------------
# mask_rows
# ---------------------------------------------------------------------------

class TestMaskRows:
    def test_full_mask_applied(self):
        rows = [_row(email="user@example.com", name="Alice")]
        it, result = mask_rows(rows, [MaskSpec(column="email", mode="full")])
        out = list(it)
        assert out[0]["email"] == "*" * len("user@example.com")
        assert out[0]["name"] == "Alice"

    def test_masked_count_incremented(self):
        rows = [
            _row(email="a@b.com"),
            _row(email="c@d.com"),
            _row(email=""),
        ]
        _, result = mask_rows(rows, [MaskSpec(column="email")])
        assert result.masked_count == 2

    def test_missing_column_skipped(self):
        rows = [_row(name="Alice")]
        _, result = mask_rows(rows, [MaskSpec(column="email")])
        assert "email" in result.skipped_columns

    def test_empty_input_returns_empty(self):
        it, result = mask_rows([], [MaskSpec(column="email")])
        assert list(it) == []
        assert result.masked_count == 0

    def test_multiple_specs_applied(self):
        rows = [_row(email="x@y.com", phone="07700900123")]
        specs = [
            MaskSpec(column="email", mode="full"),
            MaskSpec(column="phone", mode="partial", keep=4),
        ]
        it, _ = mask_rows(rows, specs)
        out = list(it)
        assert out[0]["email"] == "*" * len("x@y.com")
        assert out[0]["phone"].endswith("0123")
