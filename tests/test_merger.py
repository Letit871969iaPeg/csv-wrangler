"""Tests for csv_wrangler.merger."""
import pytest

from csv_wrangler.merger import MergeError, MergeResult, merge_rows


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# MergeResult helpers
# ---------------------------------------------------------------------------

class TestMergeResult:
    def test_total_rows_sums_source_counts(self):
        r = MergeResult(rows=[], source_counts=[3, 2])
        assert r.total_rows == 5

    def test_source_count_length(self):
        r = MergeResult(rows=[], source_counts=[1, 2, 3])
        assert r.source_count == 3

    def test_empty_result(self):
        r = MergeResult()
        assert r.total_rows == 0
        assert r.source_count == 0


# ---------------------------------------------------------------------------
# merge_rows — happy paths
# ---------------------------------------------------------------------------

def test_single_source_passthrough():
    rows = [_row(a="1", b="2"), _row(a="3", b="4")]
    result = merge_rows([rows])
    assert result.rows == rows
    assert result.source_counts == [2]


def test_two_identical_column_sources():
    s1 = [_row(name="Alice", age="30")]
    s2 = [_row(name="Bob", age="25")]
    result = merge_rows([s1, s2])
    assert len(result.rows) == 2
    assert result.rows[0]["name"] == "Alice"
    assert result.rows[1]["name"] == "Bob"


def test_source_counts_tracked_per_source():
    s1 = [_row(x="1"), _row(x="2")]
    s2 = [_row(x="3")]
    result = merge_rows([s1, s2])
    assert result.source_counts == [2, 1]


def test_empty_source_counted_as_zero():
    s1 = [_row(a="1")]
    s2: list[dict] = []
    result = merge_rows([s1, s2])
    assert result.source_counts == [1, 0]
    assert result.total_rows == 1


def test_all_empty_sources():
    result = merge_rows([[], []])
    assert result.rows == []
    assert result.total_rows == 0


# ---------------------------------------------------------------------------
# merge_rows — column mismatch handling
# ---------------------------------------------------------------------------

def test_column_mismatch_raises_by_default():
    s1 = [_row(a="1")]
    s2 = [_row(b="2")]
    with pytest.raises(MergeError, match="Column mismatch"):
        merge_rows([s1, s2])


def test_column_mismatch_no_raise_when_disabled():
    s1 = [_row(a="1")]
    s2 = [_row(b="2")]
    result = merge_rows([s1, s2], require_same_columns=False)
    assert len(result.rows) == 2


def test_fill_missing_adds_empty_values():
    s1 = [_row(a="1", b="2")]
    s2 = [_row(a="3")]
    result = merge_rows([s1, s2], fill_missing=True)
    assert result.rows[1].get("b") == ""


def test_fill_missing_custom_fill_value():
    s1 = [_row(a="1", b="2")]
    s2 = [_row(a="3")]
    result = merge_rows([s1, s2], fill_missing=True, fill_value="N/A")
    assert result.rows[1]["b"] == "N/A"


def test_fill_missing_extra_column_in_later_source():
    s1 = [_row(a="1")]
    s2 = [_row(a="2", c="extra")]
    result = merge_rows([s1, s2], fill_missing=True)
    assert "c" in result.rows[0]
    assert result.rows[0]["c"] == ""
    assert result.rows[1]["c"] == "extra"
