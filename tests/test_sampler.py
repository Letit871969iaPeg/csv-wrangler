"""Tests for csv_wrangler.sampler."""
from __future__ import annotations

import pytest

from csv_wrangler.sampler import (
    SampleError,
    SampleResult,
    reservoir_sample,
    sample_rows,
)


def _rows(n: int) -> list[dict[str, str]]:
    return [{"id": str(i), "val": str(i * 10)} for i in range(n)]


# ---------------------------------------------------------------------------
# SampleResult
# ---------------------------------------------------------------------------

class TestSampleResult:
    def test_sample_count(self):
        r = SampleResult(rows=_rows(5), total_input=20)
        assert r.sample_count == 5

    def test_empty_result(self):
        r = SampleResult()
        assert r.sample_count == 0
        assert r.total_input == 0


# ---------------------------------------------------------------------------
# sample_rows – validation
# ---------------------------------------------------------------------------

def test_neither_n_nor_fraction_raises():
    with pytest.raises(SampleError, match="exactly one"):
        sample_rows(_rows(10))


def test_both_n_and_fraction_raises():
    with pytest.raises(SampleError, match="exactly one"):
        sample_rows(_rows(10), n=3, fraction=0.5)


def test_negative_n_raises():
    with pytest.raises(SampleError, match="non-negative"):
        sample_rows(_rows(10), n=-1)


def test_fraction_out_of_range_raises():
    with pytest.raises(SampleError, match="0.0"):
        sample_rows(_rows(10), fraction=1.5)


# ---------------------------------------------------------------------------
# sample_rows – behaviour
# ---------------------------------------------------------------------------

def test_n_returns_correct_count():
    result = sample_rows(_rows(20), n=5, seed=0)
    assert result.sample_count == 5
    assert result.total_input == 20


def test_n_larger_than_population_returns_all():
    result = sample_rows(_rows(5), n=100, seed=0)
    assert result.sample_count == 5


def test_fraction_returns_proportional_count():
    result = sample_rows(_rows(100), fraction=0.1, seed=42)
    assert result.sample_count == 10


def test_fraction_zero_returns_empty():
    result = sample_rows(_rows(50), fraction=0.0)
    assert result.sample_count == 0


def test_fraction_one_returns_all():
    result = sample_rows(_rows(10), fraction=1.0)
    assert result.sample_count == 10


def test_seed_is_deterministic():
    a = sample_rows(_rows(50), n=10, seed=7)
    b = sample_rows(_rows(50), n=10, seed=7)
    assert a.rows == b.rows


def test_different_seeds_differ():
    a = sample_rows(_rows(50), n=10, seed=1)
    b = sample_rows(_rows(50), n=10, seed=2)
    assert a.rows != b.rows


def test_rows_are_subsets_of_input():
    source = _rows(30)
    result = sample_rows(source, n=10, seed=0)
    for row in result.rows:
        assert row in source


# ---------------------------------------------------------------------------
# reservoir_sample
# ---------------------------------------------------------------------------

def test_reservoir_negative_n_raises():
    with pytest.raises(SampleError, match="non-negative"):
        reservoir_sample(iter(_rows(5)), n=-1)


def test_reservoir_returns_correct_count():
    result = reservoir_sample(iter(_rows(100)), n=15, seed=0)
    assert result.sample_count == 15
    assert result.total_input == 100


def test_reservoir_n_larger_than_stream():
    result = reservoir_sample(iter(_rows(5)), n=20, seed=0)
    assert result.sample_count == 5


def test_reservoir_deterministic():
    a = reservoir_sample(iter(_rows(50)), n=10, seed=3)
    b = reservoir_sample(iter(_rows(50)), n=10, seed=3)
    assert a.rows == b.rows
