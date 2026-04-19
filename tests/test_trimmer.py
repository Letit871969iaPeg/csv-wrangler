"""Tests for csv_wrangler.trimmer."""
import pytest
from csv_wrangler.trimmer import TrimError, TrimSpec, TrimResult, trim_rows


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


class TestTrimSpec:
    def test_valid_spec_creates_ok(self):
        spec = TrimSpec(column="name")
        assert spec.column == "name"
        assert spec.chars is None
        assert spec.side == "both"

    def test_empty_column_raises(self):
        with pytest.raises(TrimError):
            TrimSpec(column="")

    def test_invalid_side_raises(self):
        with pytest.raises(TrimError):
            TrimSpec(column="x", side="center")

    def test_valid_sides_accepted(self):
        for side in ("left", "right", "both"):
            spec = TrimSpec(column="x", side=side)
            assert spec.side == side


class TestTrimResult:
    def test_defaults(self):
        r = TrimResult()
        assert r.trimmed_count == 0
        assert r.skipped_columns == []

    def test_str_no_skipped(self):
        r = TrimResult(trimmed_count=3)
        assert "trimmed=3" in str(r)
        assert "skipped" not in str(r)

    def test_str_with_skipped(self):
        r = TrimResult(trimmed_count=1, skipped_columns=["missing"])
        assert "skipped" in str(r)


class TestTrimRows:
    def test_strips_whitespace_both_sides(self):
        rows = [_row(name="  Alice  ", age="30")]
        out, result = trim_rows(rows, [TrimSpec(column="name")])
        assert out[0]["name"] == "Alice"
        assert result.trimmed_count == 1

    def test_strips_left_only(self):
        rows = [_row(name="  Alice  ")]
        out, _ = trim_rows(rows, [TrimSpec(column="name", side="left")])
        assert out[0]["name"] == "Alice  "

    def test_strips_right_only(self):
        rows = [_row(name="  Alice  ")]
        out, _ = trim_rows(rows, [TrimSpec(column="name", side="right")])
        assert out[0]["name"] == "  Alice"

    def test_strips_custom_chars(self):
        rows = [_row(code="###42###")]
        out, result = trim_rows(rows, [TrimSpec(column="code", chars="#")])
        assert out[0]["code"] == "42"
        assert result.trimmed_count == 1

    def test_no_change_not_counted(self):
        rows = [_row(name="Alice")]
        _, result = trim_rows(rows, [TrimSpec(column="name")])
        assert result.trimmed_count == 0

    def test_missing_column_skipped(self):
        rows = [_row(name="Alice")]
        _, result = trim_rows(rows, [TrimSpec(column="nonexistent")])
        assert "nonexistent" in result.skipped_columns

    def test_multiple_specs(self):
        rows = [_row(first=" A ", last=" B ")]
        specs = [TrimSpec(column="first"), TrimSpec(column="last")]
        out, result = trim_rows(rows, specs)
        assert out[0]["first"] == "A"
        assert out[0]["last"] == "B"
        assert result.trimmed_count == 2

    def test_empty_input(self):
        out, result = trim_rows([], [TrimSpec(column="name")])
        assert out == []
        assert result.trimmed_count == 0
