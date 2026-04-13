"""Tests for csv_wrangler.sorter."""

import pytest

from csv_wrangler.sorter import SortError, SortKey, parse_sort_keys, sort_rows


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rows(*dicts):
    return list(dicts)


# ---------------------------------------------------------------------------
# parse_sort_keys
# ---------------------------------------------------------------------------

class TestParseSortKeys:
    def test_bare_column_defaults_to_asc(self):
        keys = parse_sort_keys(["name"])
        assert keys == [SortKey(column="name", direction="asc")]

    def test_explicit_asc(self):
        keys = parse_sort_keys(["age:asc"])
        assert keys[0].direction == "asc"

    def test_explicit_desc(self):
        keys = parse_sort_keys(["score:desc"])
        assert keys[0].direction == "desc"

    def test_multiple_keys(self):
        keys = parse_sort_keys(["city:asc", "score:desc"])
        assert [k.column for k in keys] == ["city", "score"]
        assert [k.direction for k in keys] == ["asc", "desc"]

    def test_invalid_direction_raises(self):
        with pytest.raises(SortError, match="Invalid direction"):
            parse_sort_keys(["name:sideways"])


# ---------------------------------------------------------------------------
# sort_rows
# ---------------------------------------------------------------------------

class TestSortRows:
    def test_sort_single_column_asc(self):
        data = _rows({"name": "Charlie"}, {"name": "Alice"}, {"name": "Bob"})
        result = list(sort_rows(data, [SortKey("name")]))
        assert [r["name"] for r in result] == ["Alice", "Bob", "Charlie"]

    def test_sort_single_column_desc(self):
        data = _rows({"name": "Alice"}, {"name": "Charlie"}, {"name": "Bob"})
        result = list(sort_rows(data, [SortKey("name", direction="desc")]))
        assert [r["name"] for r in result] == ["Charlie", "Bob", "Alice"]

    def test_sort_numeric_strings(self):
        data = _rows({"score": "10"}, {"score": "3"}, {"score": "20"})
        # Lexicographic sort — expected behaviour for CSV strings.
        result = list(sort_rows(data, [SortKey("score")]))
        assert [r["score"] for r in result] == ["10", "20", "3"]

    def test_empty_rows_returns_empty(self):
        result = list(sort_rows([], [SortKey("name")]))
        assert result == []

    def test_missing_column_raises(self):
        data = _rows({"name": "Alice"})
        with pytest.raises(SortError, match="not found in data"):
            list(sort_rows(data, [SortKey("age")]))

    def test_multi_key_sort(self):
        data = _rows(
            {"city": "NYC", "score": "90"},
            {"city": "LA",  "score": "95"},
            {"city": "NYC", "score": "85"},
        )
        keys = parse_sort_keys(["city:asc", "score:desc"])
        result = list(sort_rows(data, keys))
        cities = [r["city"] for r in result]
        assert cities[0] == cities[1] == "NYC"
        assert result[0]["score"] == "90"
        assert result[1]["score"] == "85"

    def test_empty_values_sorted_last(self):
        data = _rows({"name": ""}, {"name": "Alice"}, {"name": ""})
        result = list(sort_rows(data, [SortKey("name")]))
        assert result[0]["name"] == "Alice"
