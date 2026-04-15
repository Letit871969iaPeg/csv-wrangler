"""Integration tests for the annotator using realistic CSV-like data."""

from __future__ import annotations

import csv
import io
from typing import Dict, List

from csv_wrangler.annotator import AnnotateSpec, annotate_rows


RAW_CSV = """name,score,city
alice,82,New York
bob,91,Chicago
carol,74,
dave,88,Los Angeles
"""


def _parse_csv(text: str) -> List[Dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text.strip())))


def _run(rows, specs):
    it, result = annotate_rows(rows, specs)
    return list(it), result


def test_row_count_preserved():
    rows = _parse_csv(RAW_CSV)
    specs = [AnnotateSpec(column="tag", expression=lambda r: "x")]
    out, result = _run(rows, specs)
    assert len(out) == 4
    assert result.row_count == 4


def test_upper_name_annotation():
    rows = _parse_csv(RAW_CSV)
    specs = [AnnotateSpec(column="upper_name", expression=lambda r: r["name"].upper())]
    out, _ = _run(rows, specs)
    assert out[0]["upper_name"] == "ALICE"
    assert out[2]["upper_name"] == "CAROL"


def test_has_city_flag():
    rows = _parse_csv(RAW_CSV)
    specs = [
        AnnotateSpec(
            column="has_city",
            expression=lambda r: "yes" if r["city"] else "no",
        )
    ]
    out, _ = _run(rows, specs)
    assert out[0]["has_city"] == "yes"
    assert out[2]["has_city"] == "no"


def test_original_columns_unchanged():
    rows = _parse_csv(RAW_CSV)
    specs = [AnnotateSpec(column="extra", expression=lambda r: "z")]
    out, _ = _run(rows, specs)
    assert out[1]["name"] == "bob"
    assert out[1]["score"] == "91"
    assert out[1]["city"] == "Chicago"


def test_added_column_listed_in_result():
    rows = _parse_csv(RAW_CSV)
    specs = [AnnotateSpec(column="grade", expression=lambda r: "pass")]
    _, result = _run(rows, specs)
    assert "grade" in result.added_columns
    assert result.overwritten_columns == []
