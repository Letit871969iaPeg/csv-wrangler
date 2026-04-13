"""Tests for csv_wrangler.differ."""

import pytest

from csv_wrangler.differ import DiffError, DiffResult, diff_rows


def _row(**kw):
    return {k: str(v) for k, v in kw.items()}


# ---------------------------------------------------------------------------
# DiffResult helpers
# ---------------------------------------------------------------------------

class TestDiffResult:
    def test_has_changes_false_when_empty(self):
        dr = DiffResult(key_column="id")
        assert not dr.has_changes

    def test_has_changes_true_when_added(self):
        dr = DiffResult(key_column="id", added=[_row(id=1, name="Alice")])
        assert dr.has_changes

    def test_summary_contains_key_column(self):
        dr = DiffResult(key_column="id")
        assert "id" in dr.summary()

    def test_summary_counts(self):
        dr = DiffResult(
            key_column="id",
            added=[_row(id=1)],
            removed=[_row(id=2), _row(id=3)],
            changed=[(_row(id=4, v="a"), _row(id=4, v="b"))],
        )
        summary = dr.summary()
        assert "Added      : 1" in summary
        assert "Removed    : 2" in summary
        assert "Changed    : 1" in summary


# ---------------------------------------------------------------------------
# diff_rows — happy paths
# ---------------------------------------------------------------------------

def test_identical_datasets_no_diff():
    rows = [_row(id=1, name="Alice"), _row(id=2, name="Bob")]
    result = diff_rows(rows, rows, key_column="id")
    assert not result.has_changes


def test_added_row_detected():
    before = [_row(id=1, name="Alice")]
    after  = [_row(id=1, name="Alice"), _row(id=2, name="Bob")]
    result = diff_rows(before, after, key_column="id")
    assert len(result.added) == 1
    assert result.added[0]["id"] == "2"
    assert not result.removed
    assert not result.changed


def test_removed_row_detected():
    before = [_row(id=1, name="Alice"), _row(id=2, name="Bob")]
    after  = [_row(id=1, name="Alice")]
    result = diff_rows(before, after, key_column="id")
    assert len(result.removed) == 1
    assert result.removed[0]["id"] == "2"


def test_changed_row_detected():
    before = [_row(id=1, name="Alice")]
    after  = [_row(id=1, name="Alicia")]
    result = diff_rows(before, after, key_column="id")
    assert len(result.changed) == 1
    old, new = result.changed[0]
    assert old["name"] == "Alice"
    assert new["name"] == "Alicia"


def test_empty_before_all_added():
    after = [_row(id=i) for i in range(3)]
    result = diff_rows([], after, key_column="id")
    assert len(result.added) == 3
    assert not result.removed


def test_empty_after_all_removed():
    before = [_row(id=i) for i in range(3)]
    result = diff_rows(before, [], key_column="id")
    assert len(result.removed) == 3
    assert not result.added


# ---------------------------------------------------------------------------
# diff_rows — error paths
# ---------------------------------------------------------------------------

def test_missing_key_in_before_raises():
    with pytest.raises(DiffError, match="before-row"):
        diff_rows([{"name": "Alice"}], [], key_column="id")


def test_missing_key_in_after_raises():
    with pytest.raises(DiffError, match="after-row"):
        diff_rows([], [{"name": "Bob"}], key_column="id")


def test_duplicate_key_in_before_raises():
    rows = [_row(id=1, name="Alice"), _row(id=1, name="Duplicate")]
    with pytest.raises(DiffError, match="Duplicate key"):
        diff_rows(rows, [], key_column="id")


def test_duplicate_key_in_after_raises():
    rows = [_row(id=1, name="Alice"), _row(id=1, name="Duplicate")]
    with pytest.raises(DiffError, match="Duplicate key"):
        diff_rows([], rows, key_column="id")
