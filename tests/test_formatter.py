"""Tests for csv_wrangler.formatter."""
import json
import csv
import io

from csv_wrangler.summarizer import summarize_rows
from csv_wrangler.formatter import format_summary


def _make_summary():
    rows = [
        {"name": "Alice", "age": "30"},
        {"name": "Bob", "age": ""},
        {"name": "Alice", "age": "25"},
    ]
    return summarize_rows(rows)


class TestFormatText:
    def test_contains_row_count(self):
        s = _make_summary()
        out = format_summary(s, fmt="text")
        assert "Rows: 3" in out

    def test_contains_column_names(self):
        s = _make_summary()
        out = format_summary(s, fmt="text")
        assert "name" in out
        assert "age" in out

    def test_fill_rate_shown(self):
        s = _make_summary()
        out = format_summary(s, fmt="text")
        assert "%" in out


class TestFormatJson:
    def test_valid_json(self):
        s = _make_summary()
        out = format_summary(s, fmt="json")
        data = json.loads(out)
        assert data["row_count"] == 3

    def test_columns_present(self):
        s = _make_summary()
        data = json.loads(format_summary(s, fmt="json"))
        assert "name" in data["columns"]
        assert "age" in data["columns"]

    def test_fill_rate_is_float(self):
        s = _make_summary()
        data = json.loads(format_summary(s, fmt="json"))
        assert isinstance(data["columns"]["name"]["fill_rate"], float)

    def test_top_values_list(self):
        s = _make_summary()
        data = json.loads(format_summary(s, fmt="json"))
        top = data["columns"]["name"]["top_values"]
        assert isinstance(top, list)
        assert top[0]["value"] == "Alice"
        assert top[0]["count"] == 2


class TestFormatCsv:
    def _parse(self, text):
        return list(csv.DictReader(io.StringIO(text)))

    def test_has_header(self):
        s = _make_summary()
        out = format_summary(s, fmt="csv")
        assert "column" in out
        assert "fill_rate" in out

    def test_row_per_column(self):
        s = _make_summary()
        rows = self._parse(format_summary(s, fmt="csv"))
        names = [r["column"] for r in rows]
        assert "name" in names
        assert "age" in names

    def test_fill_rate_value(self):
        s = _make_summary()
        rows = self._parse(format_summary(s, fmt="csv"))
        name_row = next(r for r in rows if r["column"] == "name")
        assert float(name_row["fill_rate"]) == 1.0

    def test_default_format_is_text(self):
        s = _make_summary()
        assert format_summary(s) == format_summary(s, fmt="text")
