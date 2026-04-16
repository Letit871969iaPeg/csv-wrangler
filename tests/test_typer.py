"""Tests for csv_wrangler.typer."""
import pytest
from csv_wrangler.typer import infer_column_type, infer_types, ColumnTypeInfo


def _col(values, name="col"):
    return infer_column_type(name, values)


def test_infer_int():
    result = _col(["1", "2", "3", "42"])
    assert result.inferred_type == "int"


def test_infer_float():
    result = _col(["1.1", "2.2", "3.3"])
    assert result.inferred_type == "float"


def test_infer_bool():
    result = _col(["true", "false", "yes", "no"])
    assert result.inferred_type == "bool"


def test_infer_date():
    result = _col(["2024-01-01", "2023-12-31", "2022-06-15"])
    assert result.inferred_type == "date"


def test_infer_string_fallback():
    result = _col(["alice", "bob", "carol"])
    assert result.inferred_type == "string"


def test_empty_values_returns_string():
    result = _col([])
    assert result.inferred_type == "string"
    assert result.sample_count == 0
    assert result.confidence == 0.0


def test_confidence_full_match():
    result = _col(["1", "2", "3"])
    assert result.confidence == 1.0


def test_confidence_partial_match_falls_back():
    # 5 ints + 5 strings => 50% < 90%, should fall back to string
    result = _col(["1", "2", "3", "4", "5", "a", "b", "c", "d", "e"])
    assert result.inferred_type == "string"


def test_blank_values_excluded_from_sample():
    result = _col(["1", "", "2", "  ", "3"])
    assert result.inferred_type == "int"
    assert result.sample_count == 3


def test_str_representation():
    info = ColumnTypeInfo(column="age", inferred_type="int", sample_count=10, match_count=10)
    assert "age" in str(info)
    assert "int" in str(info)
    assert "100%" in str(info)


def test_infer_types_multiple_columns():
    rows = [
        {"age": "25", "name": "Alice", "score": "9.5"},
        {"age": "30", "name": "Bob", "score": "8.0"},
    ]
    result = infer_types(rows)
    assert result["age"].inferred_type == "int"
    assert result["name"].inferred_type == "string"
    assert result["score"].inferred_type == "float"


def test_infer_types_empty_returns_empty():
    assert infer_types([]) == {}
