"""Tests for csv_wrangler.profiler."""
import pytest

from csv_wrangler.profiler import ColumnProfile, profile_column, profile_rows


# ---------------------------------------------------------------------------
# profile_column
# ---------------------------------------------------------------------------

class TestProfileColumn:
    def test_fill_rate_all_present(self):
        prof = profile_column("age", ["25", "30", "22"])
        assert prof.fill_rate == 1.0

    def test_fill_rate_some_empty(self):
        prof = profile_column("age", ["25", "", "22"])
        assert pytest.approx(prof.fill_rate) == 2 / 3

    def test_fill_rate_all_empty(self):
        prof = profile_column("age", ["", ""])
        assert prof.fill_rate == 0.0

    def test_fill_rate_empty_iterable(self):
        prof = profile_column("age", [])
        assert prof.fill_rate == 0.0

    def test_total_count(self):
        prof = profile_column("x", ["a", "b", "c", "d"])
        assert prof.total == 4

    def test_unique_count(self):
        prof = profile_column("x", ["a", "b", "a", "c"])
        assert prof.unique_count == 3

    def test_min_max_length(self):
        prof = profile_column("word", ["hi", "hello", "hey"])
        assert prof.min_length == 2
        assert prof.max_length == 5

    def test_min_max_length_ignores_empty(self):
        prof = profile_column("word", ["", "abc", ""])
        assert prof.min_length == 3
        assert prof.max_length == 3

    def test_min_max_length_all_empty(self):
        prof = profile_column("word", ["", ""])
        assert prof.min_length is None
        assert prof.max_length is None

    def test_whitespace_only_treated_as_empty(self):
        prof = profile_column("col", ["   ", "value"])
        assert prof.non_empty == 1


# ---------------------------------------------------------------------------
# profile_rows
# ---------------------------------------------------------------------------

def _make_rows():
    return [
        {"name": "Alice", "age": "30", "city": "NYC"},
        {"name": "Bob",   "age": "",   "city": "LA"},
        {"name": "Carol", "age": "25", "city": "NYC"},
    ]


class TestProfileRows:
    def test_returns_profile_per_column(self):
        result = profile_rows(_make_rows())
        assert set(result.keys()) == {"name", "age", "city"}

    def test_age_fill_rate(self):
        result = profile_rows(_make_rows())
        assert pytest.approx(result["age"].fill_rate) == 2 / 3

    def test_name_fill_rate_full(self):
        result = profile_rows(_make_rows())
        assert result["name"].fill_rate == 1.0

    def test_city_unique_count(self):
        result = profile_rows(_make_rows())
        assert result["city"].unique_count == 2

    def test_explicit_columns_subset(self):
        result = profile_rows(_make_rows(), columns=["name", "age"])
        assert "city" not in result
        assert "name" in result

    def test_missing_column_defaults_to_empty(self):
        rows = [{"name": "Alice"}, {"name": "Bob"}]
        result = profile_rows(rows, columns=["name", "missing"])
        assert result["missing"].fill_rate == 0.0

    def test_empty_rows_returns_empty_dict(self):
        assert profile_rows([]) == {}
