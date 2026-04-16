"""Integration tests for stacker with realistic CSV data."""
import csv
import io
from csv_wrangler.stacker import stack_rows


def _parse_csv(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text.strip())))


SALES_CSV = """
region,q1,q2,q3,q4
North,100,200,150,300
South,80,90,110,120
East,60,70,80,90
"""


def _run():
    rows = _parse_csv(SALES_CSV)
    it, result = stack_rows(rows, id_columns=["region"], key_column="quarter", value_column="sales")
    return list(it), result


def test_output_row_count():
    out, res = _run()
    assert len(out) == 12  # 3 regions × 4 quarters
    assert res.output_rows == 12


def test_input_row_count():
    _, res = _run()
    assert res.input_rows == 3


def test_value_columns_are_quarters():
    _, res = _run()
    assert set(res.value_columns) == {"q1", "q2", "q3", "q4"}


def test_region_preserved_in_all_rows():
    out, _ = _run()
    regions = {r["region"] for r in out}
    assert regions == {"North", "South", "East"}


def test_quarter_values_correct():
    out, _ = _run()
    north_q1 = next(r for r in out if r["region"] == "North" and r["quarter"] == "q1")
    assert north_q1["sales"] == "100"


def test_no_extra_columns():
    out, _ = _run()
    assert set(out[0].keys()) == {"region", "quarter", "sales"}
