"""Tests for csv_wrangler.reorderer."""
import pytest
from csv_wrangler.reorderer import (
    ReorderError,
    ReorderResult,
    reorder_rows,
)


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


class TestReorderResult:
    def test_defaults(self):
        r = ReorderResult()
        assert r.reordered_count == 0
        assert r.skipped_columns == []

    def test_custom_values(self):
        r = ReorderResult(reordered_count=3, skipped_columns=["x"])
        assert r.reordered_count == 3
        assert r.skipped_columns == ["x"]

    def test_str_no_skipped(self):
        r = ReorderResult(reordered_count=2)
        assert "reordered=2" in str(r)
        assert "skipped" not in str(r)

    def test_str_with_skipped(self):
        r = ReorderResult(reordered_count=1, skipped_columns=["z"])
        assert "skipped" in str(r)


class TestReorderRows:
    def _run(self, rows, columns, drop_rest=False):
        result, it = reorder_rows(rows, columns, drop_rest=drop_rest)
        return result, list(it)

    def test_empty_input_returns_empty(self):
        result, out = self._run([], ["a", "b"])
        assert out == []
        assert result.reordered_count == 0

    def test_basic_reorder(self):
        rows = [_row(a="1", b="2", c="3")]
        _, out = self._run(rows, ["c", "a", "b"])
        assert list(out[0].keys()) == ["c", "a", "b"]

    def test_reorder_count(self):
        rows = [_row(a="1", b="2"), _row(a="3", b="4")]
        result, _ = self._run(rows, ["b", "a"])
        assert result.reordered_count == 2

    def test_drop_rest_excludes_unlisted(self):
        rows = [_row(a="1", b="2", c="3")]
        _, out = self._run(rows, ["a"], drop_rest=True)
        assert list(out[0].keys()) == ["a"]

    def test_keep_rest_appends_unlisted(self):
        rows = [_row(a="1", b="2", c="3")]
        _, out = self._run(rows, ["c", "a"], drop_rest=False)
        assert "b" in out[0]
        assert list(out[0].keys())[0] == "c"

    def test_skipped_columns_recorded_when_drop_rest(self):
        rows = [_row(a="1", b="2", c="3")]
        result, _ = self._run(rows, ["a"], drop_rest=True)
        assert "b" in result.skipped_columns
        assert "c" in result.skipped_columns

    def test_skipped_columns_empty_when_keep_rest(self):
        rows = [_row(a="1", b="2", c="3")]
        result, _ = self._run(rows, ["a"], drop_rest=False)
        assert result.skipped_columns == []

    def test_missing_column_raises(self):
        rows = [_row(a="1", b="2")]
        with pytest.raises(ReorderError, match="not found"):
            self._run(rows, ["a", "z"])

    def test_values_preserved(self):
        rows = [_row(x="hello", y="world")]
        _, out = self._run(rows, ["y", "x"])
        assert out[0]["x"] == "hello"
        assert out[0]["y"] == "world"
