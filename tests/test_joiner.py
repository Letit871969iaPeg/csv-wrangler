"""Tests for csv_wrangler.joiner."""
import pytest
from csv_wrangler.joiner import JoinError, JoinResult, join_rows


def _row(**kwargs):
    return {k: str(v) for k, v in kwargs.items()}


LEFT = [
    _row(id="1", name="Alice"),
    _row(id="2", name="Bob"),
    _row(id="3", name="Carol"),
]

RIGHT = [
    _row(id="1", score="90"),
    _row(id="2", score="85"),
    _row(id="4", score="70"),
]


class TestInnerJoin:
    def test_matched_row_count(self):
        result = join_rows(LEFT, RIGHT, key="id")
        assert len(result.rows) == 2

    def test_merged_fields_present(self):
        result = join_rows(LEFT, RIGHT, key="id")
        row = next(r for r in result.rows if r["id"] == "1")
        assert row["name"] == "Alice"
        assert row["score"] == "90"

    def test_unmatched_rows_excluded(self):
        result = join_rows(LEFT, RIGHT, key="id")
        ids = {r["id"] for r in result.rows}
        assert "3" not in ids
        assert "4" not in ids

    def test_unmatched_counts_zero_for_inner(self):
        result = join_rows(LEFT, RIGHT, key="id")
        assert result.left_unmatched == 0
        assert result.right_unmatched == 0


class TestLeftJoin:
    def test_all_left_rows_present(self):
        result = join_rows(LEFT, RIGHT, key="id", how="left")
        ids = {r["id"] for r in result.rows}
        assert {"1", "2", "3"} == ids

    def test_unmatched_left_count(self):
        result = join_rows(LEFT, RIGHT, key="id", how="left")
        assert result.left_unmatched == 1

    def test_unmatched_row_has_no_right_fields(self):
        result = join_rows(LEFT, RIGHT, key="id", how="left")
        row = next(r for r in result.rows if r["id"] == "3")
        assert "score" not in row


class TestRightJoin:
    def test_all_right_rows_present(self):
        result = join_rows(LEFT, RIGHT, key="id", how="right")
        ids = {r["id"] for r in result.rows}
        assert "4" in ids

    def test_right_unmatched_count(self):
        result = join_rows(LEFT, RIGHT, key="id", how="right")
        assert result.right_unmatched == 1


class TestJoinErrors:
    def test_invalid_how_raises(self):
        with pytest.raises(JoinError, match="Unknown join type"):
            join_rows(LEFT, RIGHT, key="id", how="outer")

    def test_missing_key_in_left_raises(self):
        with pytest.raises(JoinError, match="left rows"):
            join_rows([_row(x="1")], RIGHT, key="id")

    def test_missing_key_in_right_raises(self):
        with pytest.raises(JoinError, match="right rows"):
            join_rows(LEFT, [_row(x="1")], key="id")

    def test_empty_iterables_returns_empty_result(self):
        result = join_rows([], [], key="id")
        assert result.rows == []
        assert result.left_unmatched == 0
        assert result.right_unmatched == 0


class TestJoinResult:
    def test_matched_property(self):
        r = JoinResult(rows=[{"id": "1"}, {"id": "2"}], left_unmatched=1, right_unmatched=0)
        assert r.matched == 1
