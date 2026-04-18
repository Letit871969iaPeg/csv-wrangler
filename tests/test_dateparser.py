"""Tests for csv_wrangler.dateparser."""
import pytest
from csv_wrangler.dateparser import DateParseError, DateSpec, DateResult, parse_dates


def _row(**kw: str) -> dict[str, str]:
    return dict(kw)


class TestDateSpec:
    def test_valid_spec_creates_ok(self):
        s = DateSpec(column="dob", out_format="%d/%m/%Y")
        assert s.column == "dob"

    def test_empty_column_raises(self):
        with pytest.raises(DateParseError):
            DateSpec(column="")

    def test_empty_out_format_raises(self):
        with pytest.raises(DateParseError):
            DateSpec(column="dob", out_format="")

    def test_dest_defaults_to_none(self):
        s = DateSpec(column="dob")
        assert s.dest is None


class TestParseDates:
    def test_iso_format_auto_detected(self):
        rows = [_row(dob="2024-03-15")]
        out, res = parse_dates(rows, [DateSpec(column="dob")])
        assert out[0]["dob"] == "2024-03-15"
        assert res.converted_count == 1

    def test_slash_format_auto_detected(self):
        rows = [_row(dob="15/03/2024")]
        out, res = parse_dates(rows, [DateSpec(column="dob")])
        assert out[0]["dob"] == "2024-03-15"
        assert res.converted_count == 1

    def test_explicit_in_format(self):
        rows = [_row(dob="03-15-2024")]
        spec = DateSpec(column="dob", in_format="%m-%d-%Y")
        out, res = parse_dates(rows, [spec])
        assert out[0]["dob"] == "2024-03-15"

    def test_custom_out_format(self):
        rows = [_row(dob="2024-03-15")]
        spec = DateSpec(column="dob", out_format="%d/%m/%Y")
        out, _ = parse_dates(rows, [spec])
        assert out[0]["dob"] == "15/03/2024"

    def test_dest_writes_new_column(self):
        rows = [_row(dob="2024-03-15")]
        spec = DateSpec(column="dob", dest="dob_formatted")
        out, _ = parse_dates(rows, [spec])
        assert "dob_formatted" in out[0]
        assert out[0]["dob"] == "2024-03-15"

    def test_invalid_value_increments_failed(self):
        rows = [_row(dob="not-a-date")]
        out, res = parse_dates(rows, [DateSpec(column="dob")])
        assert res.failed_count == 1
        assert out[0]["dob"] == "not-a-date"

    def test_empty_value_skipped(self):
        rows = [_row(dob="")]
        out, res = parse_dates(rows, [DateSpec(column="dob")])
        assert res.converted_count == 0
        assert res.failed_count == 0

    def test_multiple_specs(self):
        rows = [_row(start="2024-01-01", end="2024-12-31")]
        specs = [DateSpec(column="start"), DateSpec(column="end")]
        out, res = parse_dates(rows, specs)
        assert res.converted_count == 2

    def test_result_str(self):
        r = DateResult(converted_count=3, failed_count=1, columns_affected=["dob"])
        assert "3" in str(r) and "1" in str(r)
