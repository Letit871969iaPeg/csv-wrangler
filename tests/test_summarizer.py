"""Tests for csv_wrangler.summarizer."""
from csv_wrangler.summarizer import (
    ColumnSummary,
    DataSummary,
    summarize_rows,
    iter_summary_lines,
)


def _rows(*dicts):
    return list(dicts)


class TestColumnSummary:
    def test_fill_rate_all_filled(self):
        cs = ColumnSummary(name="x", total=4, filled=4)
        assert cs.fill_rate == 1.0

    def test_fill_rate_partial(self):
        cs = ColumnSummary(name="x", total=4, filled=2)
        assert cs.fill_rate == 0.5

    def test_fill_rate_zero_total(self):
        cs = ColumnSummary(name="x", total=0, filled=0)
        assert cs.fill_rate == 0.0

    def test_str_includes_name(self):
        cs = ColumnSummary(name="age", total=3, filled=3, top_values=[("30", 2), ("25", 1)])
        assert "age" in str(cs)
        assert "100%" in str(cs)


class TestSummarizeRows:
    def test_empty_input(self):
        result = summarize_rows([])
        assert result.row_count == 0
        assert result.columns == {}

    def test_row_count(self):
        rows = _rows({"a": "1"}, {"a": "2"}, {"a": "3"})
        result = summarize_rows(rows)
        assert result.row_count == 3

    def test_column_total(self):
        rows = _rows({"a": "x"}, {"a": "y"})
        result = summarize_rows(rows)
        assert result.columns["a"].total == 2

    def test_filled_counts_nonempty(self):
        rows = _rows({"a": "x"}, {"a": ""}, {"a": "  "})
        result = summarize_rows(rows)
        assert result.columns["a"].filled == 1

    def test_top_values_order(self):
        rows = _rows({"a": "x"}, {"a": "x"}, {"a": "y"})
        result = summarize_rows(rows)
        top = result.columns["a"].top_values
        assert top[0] == ("x", 2)
        assert top[1] == ("y", 1)

    def test_top_n_limit(self):
        rows = [{"a": str(i)} for i in range(20)]
        result = summarize_rows(rows, top_n=3)
        assert len(result.columns["a"].top_values) == 3

    def test_multiple_columns(self):
        rows = _rows({"a": "1", "b": "x"}, {"a": "2", "b": "y"})
        result = summarize_rows(rows)
        assert "a" in result.columns
        assert "b" in result.columns

    def test_str_output(self):
        rows = _rows({"name": "Alice"}, {"name": "Bob"})
        result = summarize_rows(rows)
        text = str(result)
        assert "Rows: 2" in text
        assert "name" in text


class TestIterSummaryLines:
    def test_yields_row_count_line(self):
        summary = DataSummary(row_count=7)
        lines = list(iter_summary_lines(summary))
        assert any("7" in line for line in lines)

    def test_yields_column_lines(self):
        rows = _rows({"city": "NYC"}, {"city": "LA"}, {"city": "NYC"})
        summary = summarize_rows(rows)
        lines = list(iter_summary_lines(summary))
        assert any("city" in line for line in lines)

    def test_empty_value_displayed(self):
        rows = _rows({"x": ""}, {"x": ""})
        summary = summarize_rows(rows)
        lines = list(iter_summary_lines(summary))
        assert any("(empty)" in line for line in lines)
