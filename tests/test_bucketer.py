"""Tests for csv_wrangler.bucketer."""
import pytest
from csv_wrangler.bucketer import (
    BucketError,
    BucketSpec,
    BucketResult,
    bucket_rows,
)


def _row(**kw):
    return dict(kw)


# ---------------------------------------------------------------------------
# BucketSpec validation
# ---------------------------------------------------------------------------

class TestBucketSpec:
    def test_valid_spec_creates_ok(self):
        s = BucketSpec(column="score", edges=[0, 50, 100], labels=["low", "high"])
        assert s.dest == "score_bucket"

    def test_custom_dest(self):
        s = BucketSpec(column="score", edges=[0, 50, 100], labels=["lo", "hi"], dest="tier")
        assert s.dest == "tier"

    def test_empty_column_raises(self):
        with pytest.raises(BucketError, match="column"):
            BucketSpec(column="", edges=[0, 1], labels=["x"])

    def test_too_few_edges_raises(self):
        with pytest.raises(BucketError, match="edges"):
            BucketSpec(column="v", edges=[0.0], labels=[])

    def test_label_count_mismatch_raises(self):
        with pytest.raises(BucketError, match="labels"):
            BucketSpec(column="v", edges=[0, 50, 100], labels=["only_one"])

    def test_non_increasing_edges_raises(self):
        with pytest.raises(BucketError, match="strictly increasing"):
            BucketSpec(column="v", edges=[100, 50, 0], labels=["a", "b"])

    def test_equal_edges_raises(self):
        with pytest.raises(BucketError, match="strictly increasing"):
            BucketSpec(column="v", edges=[0, 0, 100], labels=["a", "b"])


# ---------------------------------------------------------------------------
# BucketSpec.assign
# ---------------------------------------------------------------------------

class TestBucketSpecAssign:
    def _spec(self):
        return BucketSpec(column="score", edges=[0.0, 50.0, 100.0], labels=["low", "high"])

    def test_lower_bound_included(self):
        assert self._spec().assign("0") == "low"

    def test_midpoint_low_bucket(self):
        assert self._spec().assign("25") == "low"

    def test_boundary_between_buckets(self):
        assert self._spec().assign("50") == "high"

    def test_upper_bound_included(self):
        assert self._spec().assign("100") == "high"

    def test_above_range_returns_default(self):
        assert self._spec().assign("200") == "other"

    def test_below_range_returns_default(self):
        assert self._spec().assign("-1") == "other"

    def test_non_numeric_returns_default(self):
        assert self._spec().assign("n/a") == "other"

    def test_empty_string_returns_default(self):
        assert self._spec().assign("") == "other"


# ---------------------------------------------------------------------------
# bucket_rows
# ---------------------------------------------------------------------------

class TestBucketRows:
    def _spec(self):
        return BucketSpec(column="score", edges=[0.0, 50.0, 100.0], labels=["low", "high"])

    def test_dest_column_added(self):
        rows = [_row(score="30")]
        it, _ = bucket_rows(rows, [self._spec()])
        result = list(it)
        assert "score_bucket" in result[0]

    def test_correct_label_assigned(self):
        rows = [_row(score="75")]
        it, _ = bucket_rows(rows, [self._spec()])
        assert list(it)[0]["score_bucket"] == "high"

    def test_result_bucketed_count(self):
        rows = [_row(score="10"), _row(score="90"), _row(score="999")]
        it, res = bucket_rows(rows, [self._spec()])
        list(it)  # consume
        assert res.bucketed_count == 2
        assert res.default_count == 1

    def test_original_columns_preserved(self):
        rows = [_row(score="10", name="Alice")]
        it, _ = bucket_rows(rows, [self._spec()])
        row = list(it)[0]
        assert row["name"] == "Alice"
        assert row["score"] == "10"

    def test_multiple_specs(self):
        s1 = BucketSpec(column="age", edges=[0, 18, 65, 120], labels=["child", "adult", "senior"])
        s2 = BucketSpec(column="score", edges=[0.0, 50.0, 100.0], labels=["low", "high"])
        rows = [_row(age="30", score="80")]
        it, res = bucket_rows(rows, [s1, s2])
        row = list(it)[0]
        assert row["age_bucket"] == "adult"
        assert row["score_bucket"] == "high"
        assert res.bucketed_count == 2

    def test_empty_rows_returns_empty(self):
        it, res = bucket_rows([], [self._spec()])
        assert list(it) == []
        assert res.bucketed_count == 0
