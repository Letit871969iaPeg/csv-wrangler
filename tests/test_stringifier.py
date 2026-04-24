"""Tests for csv_wrangler.stringifier."""
import pytest

from csv_wrangler.stringifier import (
    StringifyError,
    StringifyResult,
    StringifySpec,
    stringify_rows_with_result,
)


def _row(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# StringifySpec
# ---------------------------------------------------------------------------

class TestStringifySpec:
    def test_valid_spec_creates_ok(self):
        spec = StringifySpec(column="score", decimal_places=2)
        assert spec.dest == "score"

    def test_dest_defaults_to_column(self):
        spec = StringifySpec(column="amount")
        assert spec.dest == "amount"

    def test_custom_dest(self):
        spec = StringifySpec(column="val", dest="val_str")
        assert spec.dest == "val_str"

    def test_empty_column_raises(self):
        with pytest.raises(StringifyError):
            StringifySpec(column="")

    def test_negative_decimal_places_raises(self):
        with pytest.raises(StringifyError):
            StringifySpec(column="x", decimal_places=-1)

    def test_zero_decimal_places_ok(self):
        spec = StringifySpec(column="x", decimal_places=0)
        assert spec.decimal_places == 0


# ---------------------------------------------------------------------------
# StringifySpec.apply
# ---------------------------------------------------------------------------

class TestApply:
    def test_float_two_decimal_places(self):
        spec = StringifySpec(column="x", decimal_places=2)
        assert spec.apply("3.14159") == "3.14"

    def test_float_zero_decimal_places(self):
        spec = StringifySpec(column="x", decimal_places=0)
        assert spec.apply("9.9") == "10"

    def test_bool_true_value(self):
        spec = StringifySpec(column="flag", true_value="yes", false_value="no")
        assert spec.apply("true") == "yes"

    def test_bool_false_value(self):
        spec = StringifySpec(column="flag", true_value="yes", false_value="no")
        assert spec.apply("false") == "no"

    def test_bool_one_maps_to_true(self):
        spec = StringifySpec(column="flag")
        assert spec.apply("1") == "true"

    def test_prefix_and_suffix(self):
        spec = StringifySpec(column="x", prefix="$", suffix="!")
        assert spec.apply("42") == "$42!"

    def test_non_numeric_passthrough(self):
        spec = StringifySpec(column="x", decimal_places=2)
        assert spec.apply("hello") == "hello"


# ---------------------------------------------------------------------------
# stringify_rows_with_result
# ---------------------------------------------------------------------------

class TestStringifyRows:
    def test_converts_float_column(self):
        rows = [_row(score="3.14159", name="Alice")]
        specs = [StringifySpec(column="score", decimal_places=2)]
        out, result = stringify_rows_with_result(rows, specs)
        assert out[0]["score"] == "3.14"
        assert result.converted_count == 1

    def test_writes_to_dest_column(self):
        rows = [_row(score="1.5")]
        specs = [StringifySpec(column="score", dest="score_str", decimal_places=1)]
        out, _ = stringify_rows_with_result(rows, specs)
        assert "score_str" in out[0]
        assert out[0]["score"] == "1.5"  # original untouched

    def test_missing_column_tracked(self):
        rows = [_row(name="Bob")]
        specs = [StringifySpec(column="missing")]
        _, result = stringify_rows_with_result(rows, specs)
        assert "missing" in result.skipped_columns
        assert result.converted_count == 0

    def test_multiple_specs(self):
        rows = [_row(a="1", b="2.5")]
        specs = [
            StringifySpec(column="a", prefix="[", suffix="]"),
            StringifySpec(column="b", decimal_places=1),
        ]
        out, result = stringify_rows_with_result(rows, specs)
        assert out[0]["a"] == "[1]"
        assert out[0]["b"] == "2.5"
        assert result.converted_count == 2

    def test_result_str(self):
        r = StringifyResult(converted_count=5)
        assert "5" in str(r)
