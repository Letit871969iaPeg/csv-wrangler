"""Tests for csv_wrangler.validator."""

import pytest

from csv_wrangler.validator import ColumnSpec, ValidationError, validate_rows


def make_rows(*dicts):
    return list(dicts)


# ---------------------------------------------------------------------------
# ColumnSpec.validate
# ---------------------------------------------------------------------------

class TestColumnSpec:
    def test_required_missing(self):
        spec = ColumnSpec(name="email", required=True)
        assert spec.validate(None) != []
        assert spec.validate("") != []

    def test_required_present(self):
        spec = ColumnSpec(name="email", required=True)
        assert spec.validate("a@b.com") == []

    def test_not_required_empty(self):
        spec = ColumnSpec(name="nickname", required=False)
        assert spec.validate("") == []
        assert spec.validate(None) == []

    def test_pattern_match(self):
        spec = ColumnSpec(name="code", pattern=r"[A-Z]{3}\d{3}")
        assert spec.validate("ABC123") == []

    def test_pattern_mismatch(self):
        spec = ColumnSpec(name="code", pattern=r"[A-Z]{3}\d{3}")
        errors = spec.validate("abc123")
        assert len(errors) == 1
        assert "pattern" in errors[0]

    def test_min_length_ok(self):
        spec = ColumnSpec(name="pw", min_length=8)
        assert spec.validate("password") == []

    def test_min_length_fail(self):
        spec = ColumnSpec(name="pw", min_length=8)
        errors = spec.validate("short")
        assert any("min_length" in e for e in errors)

    def test_max_length_fail(self):
        spec = ColumnSpec(name="tag", max_length=5)
        errors = spec.validate("toolongvalue")
        assert any("max_length" in e for e in errors)

    def test_allowed_values_ok(self):
        spec = ColumnSpec(name="status", allowed_values=["active", "inactive"])
        assert spec.validate("active") == []

    def test_allowed_values_fail(self):
        spec = ColumnSpec(name="status", allowed_values=["active", "inactive"])
        errors = spec.validate("pending")
        assert any("allowed values" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_rows
# ---------------------------------------------------------------------------

class TestValidateRows:
    def test_no_failures(self):
        rows = make_rows({"name": "Alice", "age": "30"})
        specs = [ColumnSpec("name"), ColumnSpec("age")]
        failures = validate_rows(rows, specs, raise_on_failure=False)
        assert failures == []

    def test_failure_recorded(self):
        rows = make_rows({"name": "", "age": "30"})
        specs = [ColumnSpec("name", required=True)]
        failures = validate_rows(rows, specs, raise_on_failure=False)
        assert len(failures) == 1
        assert failures[0]["row_index"] == 0
        assert failures[0]["column"] == "name"

    def test_raises_on_failure(self):
        rows = make_rows({"name": ""})
        specs = [ColumnSpec("name", required=True)]
        with pytest.raises(ValidationError) as exc_info:
            validate_rows(rows, specs)
        assert exc_info.value.failures

    def test_multiple_rows_indexed(self):
        rows = make_rows(
            {"status": "active"},
            {"status": "unknown"},
            {"status": "inactive"},
        )
        specs = [ColumnSpec("status", allowed_values=["active", "inactive"])]
        failures = validate_rows(rows, specs, raise_on_failure=False)
        assert len(failures) == 1
        assert failures[0]["row_index"] == 1
