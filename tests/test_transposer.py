"""Tests for csv_wrangler.transposer."""
from __future__ import annotations

import pytest

from csv_wrangler.transposer import TransposeError, TransposeResult, transpose_rows


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# TransposeResult unit tests
# ---------------------------------------------------------------------------

class TestTransposeResult:
    def test_defaults(self):
        r = TransposeResult()
        assert r.rows_in == 0
        assert r.columns_in == 0
        assert r.rows_out == 0
        assert r.columns_out == 0
        assert r.output_rows == []

    def test_output_rows_returns_copy(self):
        r = TransposeResult(_rows=[{"field": "x", "row_0": "1"}])
        first = r.output_rows
        first.clear()
        assert len(r.output_rows) == 1


# ---------------------------------------------------------------------------
# transpose_rows
# ---------------------------------------------------------------------------

def test_empty_input_returns_empty_result():
    result = transpose_rows([])
    assert result.rows_in == 0
    assert result.rows_out == 0
    assert result.output_rows == []


def test_single_row_single_column():
    result = transpose_rows([_row(name="Alice")])
    assert result.rows_in == 1
    assert result.columns_in == 1
    assert result.rows_out == 1
    assert result.columns_out == 2  # 'field' + 'row_0'
    assert result.output_rows[0] == {"field": "name", "row_0": "Alice"}


def test_single_row_multiple_columns():
    result = transpose_rows([_row(a="1", b="2", c="3")])
    rows = result.output_rows
    assert len(rows) == 3
    assert rows[0] == {"field": "a", "row_0": "1"}
    assert rows[1] == {"field": "b", "row_0": "2"}
    assert rows[2] == {"field": "c", "row_0": "3"}


def test_multiple_rows_multiple_columns():
    src = [
        _row(name="Alice", age="30"),
        _row(name="Bob", age="25"),
    ]
    result = transpose_rows(src)
    assert result.rows_in == 2
    assert result.columns_in == 2
    assert result.rows_out == 2
    assert result.columns_out == 3  # 'field' + 'row_0' + 'row_1'
    rows = result.output_rows
    assert rows[0] == {"field": "name", "row_0": "Alice", "row_1": "Bob"}
    assert rows[1] == {"field": "age", "row_0": "30", "row_1": "25"}


def test_custom_index_column():
    result = transpose_rows([_row(x="1")], index_column="column_name")
    assert result.output_rows[0]["column_name"] == "x"


def test_index_column_clash_raises():
    with pytest.raises(TransposeError, match="clashes"):
        transpose_rows([_row(field="v")], index_column="field")


def test_missing_value_filled_with_empty_string():
    """Rows with missing keys should produce empty strings (not KeyError)."""
    src = [
        {"a": "1", "b": "2"},
        {"a": "3"},  # 'b' absent
    ]
    result = transpose_rows(src)
    rows = result.output_rows
    b_row = next(r for r in rows if r["field"] == "b")
    assert b_row["row_1"] == ""


def test_row_labels_are_sequential():
    src = [_row(v=str(i)) for i in range(5)]
    result = transpose_rows(src)
    first_row = result.output_rows[0]
    for):
        assert f"row_{i}" in first_row
