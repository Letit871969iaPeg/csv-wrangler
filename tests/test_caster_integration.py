"""Integration tests: cast_rows over realistic CSV-like data."""
from __future__ import annotations

import csv
import io
import textwrap
from datetime import date

import pytest

from csv_wrangler.caster import CastError, CastSpec, cast_rows


CSV_DATA = textwrap.dedent("""\
    id,name,score,active,joined
    1,Alice,9.5,true,2021-06-01
    2,Bob,7.0,false,2022-11-15
    3,Carol,8.25,yes,2020-01-30
""")


def _parse_csv(text: str):
    return list(csv.DictReader(io.StringIO(text)))


SPECS = [
    CastSpec(column="id", target_type="int"),
    CastSpec(column="score", target_type="float"),
    CastSpec(column="active", target_type="bool"),
    CastSpec(column="joined", target_type="date"),
]


def test_all_types_cast_correctly():
    rows = _parse_csv(CSV_DATA)
    result = list(cast_rows(rows, SPECS))

    assert result[0]["id"] == 1
    assert result[1]["id"] == 2

    assert result[0]["score"] == pytest.approx(9.5)
    assert result[2]["score"] == pytest.approx(8.25)

    assert result[0]["active"] is True
    assert result[1]["active"] is False
    assert result[2]["active"] is True

    assert result[0]["joined"] == date(2021, 6, 1)
    assert result[1]["joined"] == date(2022, 11, 15)


def test_untouched_columns_remain_strings():
    rows = _parse_csv(CSV_DATA)
    result = list(cast_rows(rows, SPECS))
    for row in result:
        assert isinstance(row["name"], str)


def test_row_count_preserved():
    rows = _parse_csv(CSV_DATA)
    result = list(cast_rows(rows, SPECS))
    assert len(result) == 3


def test_strict_failure_propagates():
    rows = [{"score": "N/A"}]
    specs = [CastSpec(column="score", target_type="float", strict=True)]
    with pytest.raises(CastError, match="cannot cast"):
        list(cast_rows(rows, specs))


def test_lenient_failure_preserves_value():
    rows = [{"score": "N/A"}]
    specs = [CastSpec(column="score", target_type="float", strict=False)]
    result = list(cast_rows(rows, specs))
    assert result[0]["score"] == "N/A"
