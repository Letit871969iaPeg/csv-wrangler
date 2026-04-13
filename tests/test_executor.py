"""Tests for csv_wrangler.executor."""

import pytest
from csv_wrangler.parser import Rule
from csv_wrangler.executor import apply_rule, apply_rules, ExecutionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_row(**kwargs):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# apply_rule – rename
# ---------------------------------------------------------------------------

def test_rename_renames_key():
    row = make_row(first_name="Alice")
    result = apply_rule(Rule("rename", ["first_name", "name"]), row)
    assert "name" in result
    assert "first_name" not in result
    assert result["name"] == "Alice"


def test_rename_missing_column_raises():
    with pytest.raises(ExecutionError, match="rename"):
        apply_rule(Rule("rename", ["missing", "new"]), make_row(a="1"))


# ---------------------------------------------------------------------------
# apply_rule – drop
# ---------------------------------------------------------------------------

def test_drop_removes_column():
    row = make_row(a="1", b="2")
    result = apply_rule(Rule("drop", ["a"]), row)
    assert "a" not in result
    assert result["b"] == "2"


def test_drop_missing_column_raises():
    with pytest.raises(ExecutionError, match="drop"):
        apply_rule(Rule("drop", ["missing"]), make_row(a="1"))


# ---------------------------------------------------------------------------
# apply_rule – filter
# ---------------------------------------------------------------------------

def test_filter_keep_matching_row():
    row = make_row(status="active")
    result = apply_rule(Rule("filter", ["status", "==", "active"]), row)
    assert result is not None


def test_filter_drop_non_matching_row():
    row = make_row(status="inactive")
    result = apply_rule(Rule("filter", ["status", "==", "active"]), row)
    assert result is None


def test_filter_contains():
    row = make_row(email="user@example.com")
    assert apply_rule(Rule("filter", ["email", "contains", "example"]), row) is not None
    assert apply_rule(Rule("filter", ["email", "contains", "other"]), row) is None


def test_filter_unknown_operator_raises():
    with pytest.raises(ExecutionError, match="operator"):
        apply_rule(Rule("filter", ["col", ">", "5"]), make_row(col="10"))


# ---------------------------------------------------------------------------
# apply_rule – transform
# ---------------------------------------------------------------------------

def test_transform_upper():
    row = make_row(name="alice")
    result = apply_rule(Rule("transform", ["name", "upper"]), row)
    assert result["name"] == "ALICE"


def test_transform_lower():
    row = make_row(name="ALICE")
    result = apply_rule(Rule("transform", ["name", "lower"]), row)
    assert result["name"] == "alice"


def test_transform_strip():
    row = make_row(name="  alice  ")
    result = apply_rule(Rule("transform", ["name", "strip"]), row)
    assert result["name"] == "alice"


def test_transform_unknown_function_raises():
    with pytest.raises(ExecutionError, match="unknown function"):
        apply_rule(Rule("transform", ["name", "reverse"]), make_row(name="alice"))


# ---------------------------------------------------------------------------
# apply_rules – pipeline
# ---------------------------------------------------------------------------

def test_apply_rules_pipeline():
    rows = [
        make_row(first_name="Alice", status="active", score="42"),
        make_row(first_name="bob", status="inactive", score="7"),
        make_row(first_name="  Carol  ", status="active", score="99"),
    ]
    rules = [
        Rule("filter", ["status", "==", "active"]),
        Rule("rename", ["first_name", "name"]),
        Rule("transform", ["name", "strip"]),
        Rule("drop", ["status"]),
    ]
    result = apply_rules(rules, rows)
    assert len(result) == 2
    assert result[0] == {"name": "Alice", "score": "42"}
    assert result[1] == {"name": "Carol", "score": "99"}


def test_apply_rules_empty_rows():
    assert apply_rules([Rule("drop", ["x"])], []) == []
