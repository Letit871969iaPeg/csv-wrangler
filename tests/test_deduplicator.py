"""Tests for csv_wrangler.deduplicator."""
import pytest

from csv_wrangler.deduplicator import (
    DeduplicationError,
    DeduplicationResult,
    deduplicate_rows,
)


def _row(**kwargs) -> dict:
    return dict(**kwargs)


# ---------------------------------------------------------------------------
# DeduplicationResult
# ---------------------------------------------------------------------------

class TestDeduplicationResult:
    def test_duplicate_count(self):
        r = DeduplicationResult(kept=[{"a": "1"}], dropped=[{"a": "1"}, {"a": "1"}])
        assert r.duplicate_count == 2

    def test_total_input(self):
        r = DeduplicationResult(kept=[{"a": "1"}], dropped=[{"a": "1"}])
        assert r.total_input == 2

    def test_empty_result(self):
        r = DeduplicationResult()
        assert r.duplicate_count == 0
        assert r.total_input == 0


# ---------------------------------------------------------------------------
# deduplicate_rows — happy path
# ---------------------------------------------------------------------------

def test_no_duplicates_keeps_all():
    rows = [_row(id="1", name="Alice"), _row(id="2", name="Bob")]
    result = deduplicate_rows(rows, key_columns=["id"])
    assert len(result.kept) == 2
    assert result.duplicate_count == 0


def test_duplicate_key_drops_second_by_default():
    rows = [
        _row(id="1", name="Alice"),
        _row(id="1", name="Alice-dup"),
        _row(id="2", name="Bob"),
    ]
    result = deduplicate_rows(rows, key_columns=["id"])
    assert len(result.kept) == 2
    assert result.duplicate_count == 1
    assert result.kept[0]["name"] == "Alice"


def test_keep_last_retains_last_occurrence():
    rows = [
        _row(id="1", name="Alice"),
        _row(id="1", name="Alice-updated"),
    ]
    result = deduplicate_rows(rows, key_columns=["id"], keep="last")
    assert len(result.kept) == 1
    assert result.kept[0]["name"] == "Alice-updated"
    assert result.duplicate_count == 1


def test_full_row_dedup_no_key_columns():
    rows = [
        _row(a="x", b="y"),
        _row(a="x", b="y"),
        _row(a="x", b="z"),
    ]
    result = deduplicate_rows(rows)
    assert len(result.kept) == 2
    assert result.duplicate_count == 1


def test_empty_input_returns_empty_result():
    result = deduplicate_rows([])
    assert result.kept == []
    assert result.dropped == []


def test_single_row_no_duplicate():
    result = deduplicate_rows([_row(id="1")])
    assert len(result.kept) == 1
    assert result.duplicate_count == 0


# ---------------------------------------------------------------------------
# deduplicate_rows — error cases
# ---------------------------------------------------------------------------

def test_invalid_keep_raises():
    with pytest.raises(DeduplicationError, match="keep must be"):
        deduplicate_rows([_row(a="1")], keep="middle")


def test_missing_key_column_raises():
    rows = [_row(name="Alice")]
    with pytest.raises(DeduplicationError, match="not found in rows"):
        deduplicate_rows(rows, key_columns=["id"])


def test_multi_column_key():
    rows = [
        _row(first="John", last="Doe", score="10"),
        _row(first="John", last="Doe", score="20"),
        _row(first="Jane", last="Doe", score="10"),
    ]
    result = deduplicate_rows(rows, key_columns=["first", "last"])
    assert len(result.kept) == 2
    assert result.duplicate_count == 1
