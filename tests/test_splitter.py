"""Tests for csv_wrangler.splitter."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

import pytest

from csv_wrangler.splitter import SplitError, SplitResult, _safe_filename, split_rows


def _rows(*dicts: Dict[str, str]) -> List[Dict[str, str]]:
    return list(dicts)


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# _safe_filename
# ---------------------------------------------------------------------------

class TestSafeFilename:
    def test_alphanumeric_unchanged(self):
        assert _safe_filename("hello123") == "hello123"

    def test_spaces_replaced(self):
        assert _safe_filename("New York") == "New_York"

    def test_empty_string_becomes_placeholder(self):
        assert _safe_filename("") == "__empty__"

    def test_allowed_special_chars_kept(self):
        assert _safe_filename("foo-bar.baz") == "foo-bar.baz"


# ---------------------------------------------------------------------------
# SplitResult
# ---------------------------------------------------------------------------

class TestSplitResult:
    def _make(self) -> SplitResult:
        return SplitResult(
            column="region",
            output_dir=Path("/tmp/out"),
            files_written={"east": 3, "west": 5},
        )

    def test_total_rows(self):
        assert self._make().total_rows == 8

    def test_file_count(self):
        assert self._make().file_count == 2


# ---------------------------------------------------------------------------
# split_rows
# ---------------------------------------------------------------------------

def test_creates_output_directory(tmp_path):
    out = tmp_path / "new_dir"
    rows = _rows({"region": "east", "val": "1"})
    split_rows(rows, column="region", output_dir=out)
    assert out.is_dir()


def test_one_file_per_distinct_value(tmp_path):
    rows = _rows(
        {"region": "east", "val": "1"},
        {"region": "west", "val": "2"},
        {"region": "east", "val": "3"},
    )
    result = split_rows(rows, column="region", output_dir=tmp_path)
    assert result.file_count == 2


def test_row_counts_correct(tmp_path):
    rows = _rows(
        {"region": "east", "val": "1"},
        {"region": "east", "val": "2"},
        {"region": "west", "val": "3"},
    )
    result = split_rows(rows, column="region", output_dir=tmp_path)
    assert result.files_written["east"] == 2
    assert result.files_written["west"] == 1


def test_output_files_are_valid_csv(tmp_path):
    rows = _rows(
        {"region": "north", "score": "10"},
        {"region": "south", "score": "20"},
    )
    split_rows(rows, column="region", output_dir=tmp_path)
    north_rows = _read_csv(tmp_path / "north.csv")
    assert north_rows == [{"region": "north", "score": "10"}]


def test_prefix_applied_to_filenames(tmp_path):
    rows = _rows({"cat": "A", "x": "1"})
    split_rows(rows, column="cat", output_dir=tmp_path, prefix="part_")
    assert (tmp_path / "part_A.csv").exists()


def test_missing_column_raises(tmp_path):
    rows = _rows({"other": "val"})
    with pytest.raises(SplitError, match="'region'"):
        split_rows(rows, column="region", output_dir=tmp_path)


def test_empty_input_produces_no_files(tmp_path):
    result = split_rows([], column="region", output_dir=tmp_path)
    assert result.file_count == 0
    assert result.total_rows == 0
