"""Tests for csv_wrangler.grouper."""
from __future__ import annotations

import pytest

from csv_wrangler.grouper import (
    GroupError,
    GroupResult,
    group_rows,
    group_rows_with_result,
)


def _row(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# GroupResult
# ---------------------------------------------------------------------------

class TestGroupResult:
    def test_defaults(self):
        r = GroupResult()
        assert r.group_count == 0
        assert r.total_rows == 0
        assert r.key_columns == []

    def test_str_shows_counts(self):
        r = GroupResult(group_count=3, total_rows=10, key_columns=["city"])
        s = str(r)
        assert "3 groups" in s
        assert "10 rows" in s
        assert "city" in s

    def test_str_no_keys(self):
        r = GroupResult(group_count=0, total_rows=0, key_columns=[])
        assert "(none)" in str(r)


# ---------------------------------------------------------------------------
# group_rows (iterator variant)
# ---------------------------------------------------------------------------

class TestGroupRows:
    def _make_rows(self):
        return [
            _row(city="NYC", name="Alice"),
            _row(city="LA",  name="Bob"),
            _row(city="NYC", name="Carol"),
            _row(city="LA",  name="Dave"),
            _row(city="NYC", name="Eve"),
        ]

    def test_empty_key_columns_raises(self):
        with pytest.raises(GroupError, match="At least one key column"):
            list(group_rows(self._make_rows(), key_columns=[]))

    def test_missing_key_column_raises(self):
        with pytest.raises(GroupError, match="country"):
            list(group_rows(self._make_rows(), key_columns=["country"]))

    def test_group_count(self):
        result = list(group_rows(self._make_rows(), key_columns=["city"]))
        assert len(result) == 2

    def test_count_values_correct(self):
        result = list(group_rows(self._make_rows(), key_columns=["city"]))
        counts = {r["city"]: int(r["_count"]) for r in result}
        assert counts["NYC"] == 3
        assert counts["LA"] == 2

    def test_custom_count_column(self):
        result = list(
            group_rows(self._make_rows(), key_columns=["city"], count_column="n")
        )
        assert all("n" in r for r in result)
        assert all("_count" not in r for r in result)

    def test_empty_input_yields_nothing(self):
        result = list(group_rows([], key_columns=["city"]))
        assert result == []


# ---------------------------------------------------------------------------
# group_rows_with_result
# ---------------------------------------------------------------------------

class TestGroupRowsWithResult:
    def _make_rows(self):
        return [
            _row(dept="Eng",  level="senior"),
            _row(dept="Eng",  level="junior"),
            _row(dept="HR",   level="senior"),
            _row(dept="Eng",  level="senior"),
        ]

    def test_returns_tuple(self):
        rows, result = group_rows_with_result(self._make_rows(), ["dept"])
        assert isinstance(rows, list)
        assert isinstance(result, GroupResult)

    def test_result_group_count(self):
        _, result = group_rows_with_result(self._make_rows(), ["dept"])
        assert result.group_count == 2

    def test_result_total_rows(self):
        _, result = group_rows_with_result(self._make_rows(), ["dept"])
        assert result.total_rows == 4

    def test_result_key_columns_stored(self):
        _, result = group_rows_with_result(self._make_rows(), ["dept", "level"])
        assert result.key_columns == ["dept", "level"]

    def test_multi_key_grouping(self):
        rows, result = group_rows_with_result(self._make_rows(), ["dept", "level"])
        assert result.group_count == 3  # Eng/senior, Eng/junior, HR/senior
