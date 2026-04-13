"""Tests for csv_wrangler.pivotter."""
import pytest

from csv_wrangler.pivotter import PivotError, PivotResult, pivot_rows


def _row(index: str, pivot: str, value: str) -> dict:
    return {"name": index, "metric": pivot, "score": value}


SAMPLE = [
    _row("alice", "math", "90"),
    _row("alice", "english", "85"),
    _row("bob", "math", "78"),
    _row("bob", "english", "92"),
    _row("carol", "math", "88"),
]


# ---------------------------------------------------------------------------
# PivotResult unit tests
# ---------------------------------------------------------------------------

class TestPivotResult:
    def test_row_count(self):
        pr = PivotResult(rows=[{"a": "1"}, {"a": "2"}])
        assert pr.row_count == 2

    def test_empty_result_row_count(self):
        pr = PivotResult()
        assert pr.row_count == 0

    def test_pivot_values_default_empty(self):
        pr = PivotResult()
        assert pr.pivot_values == []


# ---------------------------------------------------------------------------
# pivot_rows – happy-path tests
# ---------------------------------------------------------------------------

def test_pivot_produces_correct_row_count():
    result = pivot_rows(SAMPLE, "name", "metric", "score")
    # alice, bob, carol → 3 rows
    assert result.row_count == 3


def test_pivot_values_sorted_by_default():
    result = pivot_rows(SAMPLE, "name", "metric", "score")
    assert result.pivot_values == ["english", "math"]


def test_pivot_values_unsorted_when_disabled():
    result = pivot_rows(SAMPLE, "name", "metric", "score", sort_pivot_values=False)
    # Order not guaranteed but both values present
    assert set(result.pivot_values) == {"english", "math"}


def test_pivot_alice_row_has_correct_scores():
    result = pivot_rows(SAMPLE, "name", "metric", "score")
    alice = next(r for r in result.rows if r["name"] == "alice")
    assert alice["math"] == "90"
    assert alice["english"] == "85"


def test_pivot_missing_combination_uses_fill_value():
    # carol has no 'english' entry
    result = pivot_rows(SAMPLE, "name", "metric", "score", fill_value="N/A")
    carol = next(r for r in result.rows if r["name"] == "carol")
    assert carol["english"] == "N/A"


def test_pivot_missing_combination_default_fill_is_empty_string():
    result = pivot_rows(SAMPLE, "name", "metric", "score")
    carol = next(r for r in result.rows if r["name"] == "carol")
    assert carol["english"] == ""


def test_pivot_index_column_preserved():
    result = pivot_rows(SAMPLE, "name", "metric", "score")
    for row in result.rows:
        assert "name" in row


def test_pivot_metadata_stored_on_result():
    result = pivot_rows(SAMPLE, "name", "metric", "score")
    assert result.index_column == "name"
    assert result.pivot_column == "metric"
    assert result.value_column == "score"


# ---------------------------------------------------------------------------
# pivot_rows – empty input
# ---------------------------------------------------------------------------

def test_pivot_empty_input_returns_empty_result():
    result = pivot_rows([], "name", "metric", "score")
    assert result.row_count == 0
    assert result.pivot_values == []


# ---------------------------------------------------------------------------
# pivot_rows – error cases
# ---------------------------------------------------------------------------

def test_pivot_missing_index_column_raises():
    rows = [{"metric": "math", "score": "90"}]
    with pytest.raises(PivotError, match="'name'"):
        pivot_rows(rows, "name", "metric", "score")


def test_pivot_missing_pivot_column_raises():
    rows = [{"name": "alice", "score": "90"}]
    with pytest.raises(PivotError, match="'metric'"):
        pivot_rows(rows, "name", "metric", "score")


def test_pivot_missing_value_column_raises():
    rows = [{"name": "alice", "metric": "math"}]
    with pytest.raises(PivotError, match="'score'"):
        pivot_rows(rows, "name", "metric", "score")
