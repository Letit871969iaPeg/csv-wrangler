"""Integration tests: summarizer + formatter working together via pipeline-like flow."""
import io
import csv
import json
import textwrap

from csv_wrangler.summarizer import summarize_rows
from csv_wrangler.formatter import format_summary


def _csv_to_rows(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(textwrap.dedent(text).strip())))


SAMPLE_CSV = """
    id,city,score
    1,NYC,88
    2,LA,
    3,NYC,72
    4,,55
    5,LA,90
"""


def test_row_count_matches_csv():
    rows = _csv_to_rows(SAMPLE_CSV)
    summary = summarize_rows(rows)
    assert summary.row_count == 5


def test_fill_rate_city():
    rows = _csv_to_rows(SAMPLE_CSV)
    summary = summarize_rows(rows)
    # 4 out of 5 city values are non-empty
    assert summary.columns["city"].fill_rate == 0.8


def test_fill_rate_score():
    rows = _csv_to_rows(SAMPLE_CSV)
    summary = summarize_rows(rows)
    # 4 out of 5 score values are non-empty
    assert summary.columns["score"].fill_rate == 0.8


def test_top_city_is_nyc():
    rows = _csv_to_rows(SAMPLE_CSV)
    summary = summarize_rows(rows)
    top = summary.columns["city"].top_values[0]
    assert top[0] == "NYC"
    assert top[1] == 2


def test_json_round_trip():
    rows = _csv_to_rows(SAMPLE_CSV)
    summary = summarize_rows(rows)
    data = json.loads(format_summary(summary, fmt="json"))
    assert data["row_count"] == 5
    assert data["columns"]["city"]["filled"] == 4


def test_text_format_all_columns_present():
    rows = _csv_to_rows(SAMPLE_CSV)
    summary = summarize_rows(rows)
    text = format_summary(summary, fmt="text")
    for col in ("id", "city", "score"):
        assert col in text


def test_csv_format_correct_totals():
    rows = _csv_to_rows(SAMPLE_CSV)
    summary = summarize_rows(rows)
    out = format_summary(summary, fmt="csv")
    parsed = list(csv.DictReader(io.StringIO(out)))
    for row in parsed:
        assert int(row["total"]) == 5
