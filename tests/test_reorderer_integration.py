"""Integration tests for the reorderer module using realistic CSV data."""
import csv
import io
import textwrap

import pytest

from csv_wrangler.reorderer import ReorderError, reorder_rows


CSV_DATA = textwrap.dedent("""\
    id,name,city,score
    1,Alice,NYC,88
    2,Bob,LA,72
    3,Carol,Chicago,95
    4,Dave,,61
""")


def _parse_csv(data: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data)))


def test_row_count_preserved():
    rows = _parse_csv(CSV_DATA)
    _, out = reorder_rows(rows, ["score", "name", "id", "city"])
    assert len(list(out)) == 4


def test_column_order_applied():
    rows = _parse_csv(CSV_DATA)
    desired = ["score", "name", "id", "city"]
    _, out = reorder_rows(rows, desired)
    for row in out:
        assert list(row.keys())[:4] == desired


def test_drop_rest_removes_city():
    rows = _parse_csv(CSV_DATA)
    _, out = reorder_rows(rows, ["id", "name", "score"], drop_rest=True)
    for row in out:
        assert "city" not in row


def test_all_values_intact_after_reorder():
    rows = _parse_csv(CSV_DATA)
    _, out = reorder_rows(rows, ["city", "id", "name", "score"])
    out_list = list(out)
    assert out_list[0]["name"] == "Alice"
    assert out_list[2]["city"] == "Chicago"


def test_unknown_column_raises():
    rows = _parse_csv(CSV_DATA)
    with pytest.raises(ReorderError):
        reorder_rows(rows, ["id", "nonexistent"])
