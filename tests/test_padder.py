"""Tests for csv_wrangler.padder."""
from __future__ import annotations

import pytest

from csv_wrangler.padder import PadError, PadResult, PadSpec, pad_rows, _pad_value


# ---------------------------------------------------------------------------
# PadSpec validation
# ---------------------------------------------------------------------------

class TestPadSpec:
    def test_valid_spec_creates_ok(self):
        spec = PadSpec(column="name", width=10)
        assert spec.width == 10

    def test_zero_width_raises(self):
        with pytest.raises(PadError, match="width"):
            PadSpec(column="x", width=0)

    def test_multi_char_fill_raises(self):
        with pytest.raises(PadError, match="fill_char"):
            PadSpec(column="x", width=5, fill_char="ab")

    def test_invalid_side_raises(self):
        with pytest.raises(PadError, match="side"):
            PadSpec(column="x", width=5, side="center")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _pad_value
# ---------------------------------------------------------------------------

class TestPadValue:
    def test_right_pad(self):
        spec = PadSpec(column="c", width=6, fill_char="-", side="right")
        assert _pad_value("abc", spec) == "abc---"

    def test_left_pad(self):
        spec = PadSpec(column="c", width=6, fill_char="0", side="left")
        assert _pad_value("42", spec) == "000042"

    def test_both_pad_even(self):
        spec = PadSpec(column="c", width=6, fill_char="*", side="both")
        assert _pad_value("ab", spec) == "**ab**"

    def test_both_pad_odd_extra_right(self):
        spec = PadSpec(column="c", width=7, fill_char="*", side="both")
        assert _pad_value("ab", spec) == "**ab***"

    def test_already_wide_enough_unchanged(self):
        spec = PadSpec(column="c", width=3, side="right")
        assert _pad_value("hello", spec) == "hello"

    def test_truncate_long_value(self):
        spec = PadSpec(column="c", width=4, side="right", truncate=True)
        assert _pad_value("toolong", spec) == "tool"

    def test_no_truncate_leaves_long_value(self):
        spec = PadSpec(column="c", width=4, side="right", truncate=False)
        assert _pad_value("toolong", spec) == "toolong"


# ---------------------------------------------------------------------------
# pad_rows
# ---------------------------------------------------------------------------

def _rows(*dicts: dict) -> list[dict[str, str]]:
    return [dict(r) for r in dicts]


def test_pad_rows_right_pads_column():
    rows = _rows({"code": "A"}, {"code": "BC"})
    spec = PadSpec(column="code", width=4, fill_char="0", side="right")
    it, result = pad_rows(rows, [spec])
    out = list(it)
    assert out[0]["code"] == "A000"
    assert out[1]["code"] == "BC00"
    assert result.total_rows == 2
    assert result.padded_cells == 2


def test_pad_rows_no_change_when_already_wide():
    rows = _rows({"id": "12345"})
    spec = PadSpec(column="id", width=3, side="left", fill_char="0")
    it, result = pad_rows(rows, [spec])
    list(it)
    assert result.padded_cells == 0


def test_pad_rows_missing_column_raises():
    rows = _rows({"name": "Alice"})
    spec = PadSpec(column="missing", width=5)
    it, _ = pad_rows(rows, [spec])
    with pytest.raises(PadError, match="missing"):
        list(it)


def test_pad_rows_columns_affected_sorted():
    rows = _rows({"z": "a", "a": "b"})
    specs = [PadSpec(column="z", width=3), PadSpec(column="a", width=3)]
    _, result = pad_rows(rows, specs)
    list(_[0:0])  # don't consume — columns_affected set at construction
    assert result.columns_affected == ["a", "z"]


def test_pad_result_str_smoke():
    r = PadResult(total_rows=5, padded_cells=3, columns_affected=["x"])
    assert "5" in str(r)
