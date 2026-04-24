"""Tests for csv_wrangler.zipper."""
import pytest
from csv_wrangler.zipper import ZipError, ZipResult, zip_rows


def _row(**kwargs):
    return {k: str(v) for k, v in kwargs.items()}


class TestZipResult:
    def test_defaults(self):
        r = ZipResult()
        assert r.rows == []
        assert r.left_count == 0
        assert r.right_count == 0
        assert r.output_count == 0
        assert r.truncated is False

    def test_custom_values(self):
        rows = [_row(a="1")]
        r = ZipResult(rows=rows, left_count=1, right_count=1, output_count=1)
        assert r.output_count == 1
        assert r.rows is rows


class TestZipRows:
    def test_equal_length_merges_correctly(self):
        left = [_row(name="Alice"), _row(name="Bob")]
        right = [_row(score="10"), _row(score="20")]
        result = zip_rows(left, right)
        assert result.output_count == 2
        assert result.truncated is False
        assert result.rows[0] == {"left_name": "Alice", "right_score": "10"}
        assert result.rows[1] == {"left_name": "Bob", "right_score": "20"}

    def test_custom_prefixes(self):
        left = [_row(x="1")]
        right = [_row(x="2")]
        result = zip_rows(left, right, prefix_left="A_", prefix_right="B_")
        assert "A_x" in result.rows[0]
        assert "B_x" in result.rows[0]

    def test_left_longer_truncated(self):
        left = [_row(a="1"), _row(a="2"), _row(a="3")]
        right = [_row(b="x")]
        result = zip_rows(left, right)
        assert result.truncated is True
        assert result.output_count == 1
        assert result.left_count == 3
        assert result.right_count == 1

    def test_right_longer_truncated(self):
        left = [_row(a="1")]
        right = [_row(b="x"), _row(b="y")]
        result = zip_rows(left, right)
        assert result.truncated is True
        assert result.output_count == 1

    def test_strict_raises_on_mismatch(self):
        left = [_row(a="1"), _row(a="2")]
        right = [_row(b="x")]
        with pytest.raises(ZipError, match="Row count mismatch"):
            zip_rows(left, right, strict=True)

    def test_strict_ok_when_equal(self):
        left = [_row(a="1")]
        right = [_row(b="2")]
        result = zip_rows(left, right, strict=True)
        assert result.output_count == 1
        assert result.truncated is False

    def test_empty_inputs(self):
        result = zip_rows([], [])
        assert result.rows == []
        assert result.output_count == 0
        assert result.truncated is False

    def test_column_collision_resolved_by_prefix(self):
        left = [_row(id="1", name="Alice")]
        right = [_row(id="99", city="NYC")]
        result = zip_rows(left, right)
        row = result.rows[0]
        assert row["left_id"] == "1"
        assert row["right_id"] == "99"
        assert row["left_name"] == "Alice"
        assert row["right_city"] == "NYC"

    def test_counts_reflect_inputs(self):
        left = [_row(a=str(i)) for i in range(5)]
        right = [_row(b=str(i)) for i in range(5)]
        result = zip_rows(left, right)
        assert result.left_count == 5
        assert result.right_count == 5
        assert result.output_count == 5
