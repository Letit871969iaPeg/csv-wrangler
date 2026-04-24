"""Tests for csv_wrangler.ranker."""
import pytest
from csv_wrangler.ranker import RankError, RankResult, RankSpec, rank_rows


def _row(**kw: str) -> dict[str, str]:
    return dict(kw)


# ---------------------------------------------------------------------------
# RankSpec validation
# ---------------------------------------------------------------------------

class TestRankSpec:
    def test_valid_spec_creates_ok(self):
        s = RankSpec(column="score")
        assert s.column == "score"
        assert s.dest == "rank"
        assert s.method == "dense"

    def test_empty_column_raises(self):
        with pytest.raises(RankError, match="column"):
            RankSpec(column="")

    def test_empty_dest_raises(self):
        with pytest.raises(RankError, match="dest"):
            RankSpec(column="score", dest="")

    def test_invalid_method_raises(self):
        with pytest.raises(RankError, match="method"):
            RankSpec(column="score", method="average")

    def test_row_method_accepted(self):
        s = RankSpec(column="score", method="row")
        assert s.method == "row"


# ---------------------------------------------------------------------------
# RankResult
# ---------------------------------------------------------------------------

class TestRankResult:
    def test_defaults(self):
        r = RankResult()
        assert r.ranked_count == 0
        assert r.skipped_count == 0

    def test_str(self):
        r = RankResult(ranked_count=5, skipped_count=1)
        assert "5" in str(r)
        assert "1" in str(r)


# ---------------------------------------------------------------------------
# rank_rows – dense method
# ---------------------------------------------------------------------------

def test_dense_rank_ascending():
    rows = [
        _row(name="a", score="10"),
        _row(name="b", score="20"),
        _row(name="c", score="10"),
        _row(name="d", score="30"),
    ]
    out, res = rank_rows(rows, RankSpec(column="score"))
    ranks = {r["name"]: r["rank"] for r in out}
    assert ranks["a"] == "1"
    assert ranks["c"] == "1"
    assert ranks["b"] == "2"
    assert ranks["d"] == "3"
    assert res.ranked_count == 4
    assert res.skipped_count == 0


def test_dense_rank_descending():
    rows = [
        _row(score="10"),
        _row(score="30"),
        _row(score="20"),
    ]
    out, _ = rank_rows(rows, RankSpec(column="score", ascending=False))
    scores_to_rank = {r["score"]: r["rank"] for r in out}
    assert scores_to_rank["30"] == "1"
    assert scores_to_rank["20"] == "2"
    assert scores_to_rank["10"] == "3"


def test_row_method_no_ties():
    rows = [_row(score="5"), _row(score="15"), _row(score="10")]
    out, res = rank_rows(rows, RankSpec(column="score", method="row"))
    assert res.ranked_count == 3
    ranks = {r["score"]: int(r["rank"]) for r in out}
    assert ranks["5"] < ranks["10"] < ranks["15"]


def test_skipped_non_numeric():
    rows = [_row(score="abc"), _row(score="10")]
    out, res = rank_rows(rows, RankSpec(column="score"))
    assert res.skipped_count == 1
    assert res.ranked_count == 1
    assert "rank" not in out[0] or out[0].get("rank", "") == ""


def test_grouped_ranking():
    rows = [
        _row(group="A", score="10"),
        _row(group="A", score="20"),
        _row(group="B", score="5"),
        _row(group="B", score="15"),
    ]
    out, res = rank_rows(rows, RankSpec(column="score", group_by="group"))
    assert res.ranked_count == 4
    # Within each group rank starts at 1
    a_rows = [r for r in out if r["group"] == "A"]
    b_rows = [r for r in out if r["group"] == "B"]
    assert {r["rank"] for r in a_rows} == {"1", "2"}
    assert {r["rank"] for r in b_rows} == {"1", "2"}


def test_custom_dest_column():
    rows = [_row(score="1"), _row(score="2")]
    out, _ = rank_rows(rows, RankSpec(column="score", dest="position"))
    assert "position" in out[0]
    assert "rank" not in out[0]
