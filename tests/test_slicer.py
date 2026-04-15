"""Tests for csv_wrangler.slicer."""
import pytest

from csv_wrangler.slicer import SliceError, SliceResult, slice_rows


def _rows(n: int) -> list[dict]:
    return [{"id": str(i), "val": str(i * 10)} for i in range(n)]


# ---------------------------------------------------------------------------
# SliceResult
# ---------------------------------------------------------------------------

class TestSliceResult:
    def test_kept_count(self):
        r = SliceResult(rows=[{"a": "1"}, {"a": "2"}], total_input=5)
        assert r.kept_count == 2

    def test_skipped_count(self):
        r = SliceResult(rows=[{"a": "1"}], total_input=5)
        assert r.skipped_count == 4

    def test_empty_result(self):
        r = SliceResult()
        assert r.kept_count == 0
        assert r.skipped_count == 0


# ---------------------------------------------------------------------------
# slice_rows – happy paths
# ---------------------------------------------------------------------------

def test_default_keeps_all_rows():
    result = slice_rows(_rows(5))
    assert result.kept_count == 5
    assert result.total_input == 5


def test_start_skips_leading_rows():
    result = slice_rows(_rows(5), start=2)
    assert [r["id"] for r in result.rows] == ["2", "3", "4"]


def test_end_limits_trailing_rows():
    result = slice_rows(_rows(5), end=3)
    assert [r["id"] for r in result.rows] == ["0", "1", "2"]


def test_start_and_end_window():
    result = slice_rows(_rows(10), start=3, end=7)
    assert [r["id"] for r in result.rows] == ["3", "4", "5", "6"]


def test_start_equals_last_index_keeps_one_row():
    result = slice_rows(_rows(5), start=4)
    assert result.kept_count == 1
    assert result.rows[0]["id"] == "4"


def test_end_beyond_length_clamps_gracefully():
    result = slice_rows(_rows(3), end=100)
    assert result.kept_count == 3


def test_empty_source():
    result = slice_rows([], start=0, end=5)
    assert result.kept_count == 0
    assert result.total_input == 0


def test_rows_are_copies():
    source = _rows(3)
    result = slice_rows(source)
    result.rows[0]["id"] = "mutated"
    assert source[0]["id"] == "0"


# ---------------------------------------------------------------------------
# slice_rows – error paths
# ---------------------------------------------------------------------------

def test_negative_start_raises():
    with pytest.raises(SliceError, match="start must be"):
        slice_rows(_rows(5), start=-1)


def test_end_equal_to_start_raises():
    with pytest.raises(SliceError, match="end"):
        slice_rows(_rows(5), start=2, end=2)


def test_end_less_than_start_raises():
    with pytest.raises(SliceError, match="end"):
        slice_rows(_rows(5), start=4, end=2)
