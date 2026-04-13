"""Tests for csv_wrangler.renamer."""
from __future__ import annotations

import pytest

from csv_wrangler.renamer import RenameError, RenameResult, rename_rows


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# RenameResult
# ---------------------------------------------------------------------------

class TestRenameResult:
    def test_renamed_count_default(self):
        r = RenameResult()
        assert r.renamed_count == 0

    def test_skipped_columns_default_empty(self):
        r = RenameResult()
        assert r.skipped_columns == []

    def test_custom_values(self):
        r = RenameResult(renamed_count=3, skipped_columns=["x"])
        assert r.renamed_count == 3
        assert r.skipped_columns == ["x"]


# ---------------------------------------------------------------------------
# rename_rows – error cases
# ---------------------------------------------------------------------------

def test_empty_mapping_raises():
    with pytest.raises(RenameError, match="mapping must contain"):
        rename_rows([], {})


def test_duplicate_target_names_raises():
    rows = [_row(a="1", b="2")]
    with pytest.raises(RenameError, match="duplicate target"):
        rename_rows(rows, {"a": "z", "b": "z"})


def test_strict_mode_missing_column_raises():
    rows = [_row(a="1")]
    with pytest.raises(RenameError, match="strict mode"):
        rename_rows(rows, {"missing": "new"}, strict=True)


# ---------------------------------------------------------------------------
# rename_rows – happy path
# ---------------------------------------------------------------------------

def test_basic_rename():
    rows = [_row(first_name="Alice", age="30")]
    it, result = rename_rows(rows, {"first_name": "name"})
    out = list(it)
    assert out[0]["name"] == "Alice"
    assert "first_name" not in out[0]
    assert result.renamed_count == 1
    assert result.skipped_columns == []


def test_multiple_renames():
    rows = [_row(a="1", b="2", c="3")]
    it, result = rename_rows(rows, {"a": "x", "b": "y"})
    out = list(it)
    assert out[0] == {"x": "1", "y": "2", "c": "3"}
    assert result.renamed_count == 2


def test_non_strict_skips_missing_column():
    rows = [_row(a="1")]
    it, result = rename_rows(rows, {"a": "alpha", "missing": "gone"}, strict=False)
    out = list(it)
    assert out[0] == {"alpha": "1"}
    assert result.skipped_columns == ["missing"]
    assert result.renamed_count == 1


def test_empty_rows_returns_empty_iterator():
    it, result = rename_rows([], {"a": "b"})
    assert list(it) == []
    assert result.renamed_count == 0


def test_multiple_rows_all_renamed():
    rows = [
        _row(city="NYC", pop="8m"),
        _row(city="LA", pop="4m"),
    ]
    it, result = rename_rows(rows, {"city": "location", "pop": "population"})
    out = list(it)
    assert all("location" in r and "population" in r for r in out)
    assert result.renamed_count == 2


def test_untouched_columns_preserved():
    rows = [_row(keep="yes", rename_me="old")]
    it, _ = rename_rows(rows, {"rename_me": "new"})
    out = list(it)
    assert out[0]["keep"] == "yes"
    assert out[0]["new"] == "old"
