"""Tests for the csv-wrangler DSL parser."""

import pytest
from csv_wrangler.parser import Rule, ParseError, parse_rule, parse_rules


class TestParseRule:
    def test_rename_valid(self):
        rule = parse_rule("rename old_col -> new_col")
        assert rule == Rule(operation="rename", column="old_col", value="new_col")

    def test_drop_valid(self):
        rule = parse_rule("drop unwanted_column")
        assert rule == Rule(operation="drop", column="unwanted_column")

    def test_filter_valid(self):
        rule = parse_rule("filter age > 18")
        assert rule == Rule(operation="filter", column="age", expression="> 18")

    def test_transform_valid(self):
        rule = parse_rule("transform price * 1.1")
        assert rule == Rule(operation="transform", column="price", expression="* 1.1")

    def test_validate_valid(self):
        rule = parse_rule(r"validate email ~= ^[\w.+-]+@[\w-]+\.[\w.]+$")
        assert rule.operation == "validate"
        assert rule.column == "email"
        assert rule.expression is not None

    def test_operation_case_insensitive(self):
        rule = parse_rule("DROP my_col")
        assert rule.operation == "drop"

    def test_unknown_operation_raises(self):
        with pytest.raises(ParseError, match="Unknown operation"):
            parse_rule("explode some_col")

    def test_rename_missing_arrow_raises(self):
        with pytest.raises(ParseError, match="rename expects"):
            parse_rule("rename old_col new_col")

    def test_filter_missing_expression_raises(self):
        with pytest.raises(ParseError, match="filter expects"):
            parse_rule("filter column_only")

    def test_empty_line_raises(self):
        with pytest.raises(ParseError):
            parse_rule("")

    def test_comment_line_raises(self):
        with pytest.raises(ParseError):
            parse_rule("# this is a comment")

    def test_missing_column_raises(self):
        with pytest.raises(ParseError):
            parse_rule("drop")


class TestParseRules:
    DSL_TEXT = """
# Example transformation rules
rename first_name -> name
drop internal_id
filter age >= 0
transform salary * 1.05
validate email ~= .+@.+
"""

    def test_parses_multiple_rules(self):
        rules = parse_rules(self.DSL_TEXT)
        assert len(rules) == 5

    def test_skips_comments_and_blanks(self):
        rules = parse_rules("\n# comment\n\ndrop col\n")
        assert len(rules) == 1

    def test_error_includes_line_number(self):
        bad_dsl = "drop col1\nexplode col2\n"
        with pytest.raises(ParseError, match="Line 2"):
            parse_rules(bad_dsl)

    def test_empty_string_returns_empty_list(self):
        assert parse_rules("") == []

    def test_only_comments_returns_empty_list(self):
        assert parse_rules("# nothing here\n# nope") == []
