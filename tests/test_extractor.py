"""Tests for csv_wrangler.extractor."""
import pytest
from csv_wrangler.extractor import (
    ExtractError,
    ExtractSpec,
    ExtractResult,
    extract_rows,
)


def _row(**kwargs: str) -> dict[str, str]:
    return dict(kwargs)


class TestExtractSpec:
    def test_valid_spec_creates_ok(self):
        spec = ExtractSpec(column="email", pattern=r"@(.+)")
        assert spec.column == "email"
        assert spec.dest == "email"  # defaults to column

    def test_custom_dest(self):
        spec = ExtractSpec(column="url", pattern=r"https://([^/]+)", dest="domain")
        assert spec.dest == "domain"

    def test_empty_column_raises(self):
        with pytest.raises(ExtractError, match="column"):
            ExtractSpec(column="", pattern=r"\d+")

    def test_empty_pattern_raises(self):
        with pytest.raises(ExtractError, match="pattern"):
            ExtractSpec(column="col", pattern="")

    def test_invalid_regex_raises(self):
        with pytest.raises(ExtractError, match="invalid regex"):
            ExtractSpec(column="col", pattern="[unclosed")

    def test_zero_group_raises(self):
        with pytest.raises(ExtractError, match="group"):
            ExtractSpec(column="col", pattern=r"(\d+)", group=0)


class TestExtractResult:
    def test_defaults(self):
        r = ExtractResult()
        assert r.matched_count == 0
        assert r.unmatched_count == 0
        assert r.specs == []

    def test_str_shows_counts(self):
        r = ExtractResult(matched_count=3, unmatched_count=1)
        s = str(r)
        assert "matched=3" in s
        assert "unmatched=1" in s


class TestExtractRows:
    def _run(self, rows, specs):
        it, result = extract_rows(iter(rows), specs)
        return list(it), result

    def test_basic_extraction(self):
        rows = [_row(email="user@example.com"), _row(email="admin@corp.org")]
        spec = ExtractSpec(column="email", pattern=r"@(.+)", dest="domain")
        out, result = self._run(rows, [spec])
        assert out[0]["domain"] == "example.com"
        assert out[1]["domain"] == "corp.org"
        assert result.matched_count == 2
        assert result.unmatched_count == 0

    def test_no_match_writes_on_no_match_value(self):
        rows = [_row(phone="no-number-here")]
        spec = ExtractSpec(column="phone", pattern=r"(\d{10})", dest="digits", on_no_match="N/A")
        out, result = self._run(rows, [spec])
        assert out[0]["digits"] == "N/A"
        assert result.unmatched_count == 1

    def test_dest_defaults_overwrites_source_column(self):
        rows = [_row(code="ABC-123")]
        spec = ExtractSpec(column="code", pattern=r"([A-Z]+)")
        out, _ = self._run(rows, [spec])
        assert out[0]["code"] == "ABC"

    def test_missing_column_raises(self):
        rows = [_row(name="Alice")]
        spec = ExtractSpec(column="missing", pattern=r"(\w+)")
        with pytest.raises(ExtractError, match="column not found"):
            it, _ = extract_rows(iter(rows), [spec])
            list(it)

    def test_no_specs_raises(self):
        with pytest.raises(ExtractError, match="at least one"):
            extract_rows(iter([]), [])

    def test_original_columns_preserved(self):
        rows = [_row(name="Alice", email="alice@x.com")]
        spec = ExtractSpec(column="email", pattern=r"@(.+)", dest="domain")
        out, _ = self._run(rows, [spec])
        assert out[0]["name"] == "Alice"
        assert out[0]["email"] == "alice@x.com"
