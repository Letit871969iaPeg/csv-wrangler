"""Integration tests for date parsing over realistic CSV data."""
import csv
import io
import textwrap

from csv_wrangler.dateparser import DateSpec, parse_dates


def _parse_csv(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(textwrap.dedent(text).strip())))


SAMPLE = """\
id,name,joined,last_seen
1,Alice,2022-01-15,15/06/2023
2,Bob,2021-11-03,03/03/2022
3,Carol,2023-07-22,
"""


def test_row_count_preserved():
    rows = _parse_csv(SAMPLE)
    specs = [DateSpec(column="joined"), DateSpec(column="last_seen")]
    out, _ = parse_dates(rows, specs)
    assert len(out) == 3


def test_joined_dates_normalized():
    rows = _parse_csv(SAMPLE)
    out, _ = parse_dates(rows, [DateSpec(column="joined")])
    assert out[0]["joined"] == "2022-01-15"
    assert out[1]["joined"] == "2021-11-03"


def test_slash_dates_normalized():
    rows = _parse_csv(SAMPLE)
    out, _ = parse_dates(rows, [DateSpec(column="last_seen")])
    assert out[0]["last_seen"] == "2023-06-15"
    assert out[1]["last_seen"] == "2022-03-03"


def test_empty_value_not_counted():
    rows = _parse_csv(SAMPLE)
    out, res = parse_dates(rows, [DateSpec(column="last_seen")])
    assert res.converted_count == 2
    assert res.failed_count == 0


def test_untouched_columns_intact():
    rows = _parse_csv(SAMPLE)
    out, _ = parse_dates(rows, [DateSpec(column="joined")])
    assert out[0]["name"] == "Alice"
    assert out[2]["id"] == "3"


def test_dest_does_not_overwrite_source():
    rows = _parse_csv(SAMPLE)
    specs = [DateSpec(column="joined", out_format="%d/%m/%Y", dest="joined_eu")]
    out, _ = parse_dates(rows, specs)
    assert out[0]["joined"] == "2022-01-15"
    assert out[0]["joined_eu"] == "15/01/2022"
