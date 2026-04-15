"""Tests for csv_wrangler.replacer."""
import pytest
from csv_wrangler.replacer import (
    ReplaceError,
    ReplaceSpec,
    ReplaceResult,
    replace_rows,
    _iter,
)


def _row(**kwargs):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# ReplaceSpec
# ---------------------------------------------------------------------------

class TestReplaceSpec:
    def test_valid_spec_creates_ok(self):
        spec = ReplaceSpec(column="name", find="foo", replacement="bar")
        assert spec.column == "name"

    def test_empty_column_raises(self):
        with pytest.raises(ReplaceError):
            ReplaceSpec(column="", find="x", replacement="y")

    def test_whole_cell_defaults_false(self):
        spec = ReplaceSpec(column="c", find="a", replacement="b")
        assert spec.whole_cell is False


# ---------------------------------------------------------------------------
# replace_rows — basic
# ---------------------------------------------------------------------------

def test_empty_rows_returns_empty():
    result, summary = replace_rows([], [ReplaceSpec("name", "a", "b")])
    assert result == []
    assert summary.replaced_count == 0


def test_substring_replacement():
    rows = [_row(name="foobar"), _row(name="baz")]
    out, summary = replace_rows(rows, [ReplaceSpec("name", "foo", "qux")])
    assert out[0]["name"] == "quxbar"
    assert out[1]["name"] == "baz"
    assert summary.replaced_count == 1


def test_whole_cell_only_replaces_exact_match():
    rows = [_row(city="New York"), _row(city="New York City")]
    spec = ReplaceSpec("city", "New York", "NYC", whole_cell=True)
    out, summary = replace_rows(rows, [spec])
    assert out[0]["city"] == "NYC"
    assert out[1]["city"] == "New York City"  # not replaced
    assert summary.replaced_count == 1


def test_missing_column_recorded_in_skipped():
    rows = [_row(name="Alice")]
    _, summary = replace_rows(rows, [ReplaceSpec("missing", "x", "y")])
    assert "missing" in summary.skipped_columns
    assert summary.replaced_count == 0


def test_multiple_specs_applied_in_order():
    rows = [_row(val="aabbcc")]
    specs = [
        ReplaceSpec("val", "aa", "XX"),
        ReplaceSpec("val", "cc", "ZZ"),
    ]
    out, summary = replace_rows(rows, specs)
    assert out[0]["val"] == "XXbbZZ"
    assert summary.replaced_count == 2


def test_no_match_does_not_increment_count():
    rows = [_row(name="hello")]
    _, summary = replace_rows(rows, [ReplaceSpec("name", "xyz", "abc")])
    assert summary.replaced_count == 0


def test_original_rows_not_mutated():
    original = [_row(name="foo")]
    replace_rows(original, [ReplaceSpec("name", "foo", "bar")])
    assert original[0]["name"] == "foo"


def test_skipped_column_deduplicated():
    rows = [_row(a="1")]
    specs = [ReplaceSpec("missing", "x", "y"), ReplaceSpec("missing", "a", "b")]
    _, summary = replace_rows(rows, specs)
    assert summary.skipped_columns.count("missing") == 1


# ---------------------------------------------------------------------------
# _iter streaming
# ---------------------------------------------------------------------------

def test_iter_yields_all_rows():
    rows = [_row(x="hello"), _row(x="world")]
    result = list(_iter(rows, [ReplaceSpec("x", "o", "0")]))
    assert len(result) == 2


def test_iter_applies_replacement():
    rows = [_row(x="hello world")]
    result = list(_iter(rows, [ReplaceSpec("x", "world", "there")]))
    assert result[0]["x"] == "hello there"


def test_iter_skips_missing_column_silently():
    rows = [_row(a="1")]
    result = list(_iter(rows, [ReplaceSpec("b", "x", "y")]))
    assert result[0] == {"a": "1"}
