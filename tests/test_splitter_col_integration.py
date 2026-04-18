"""Integration tests for column splitting on realistic CSV data."""
import csv
import io
import textwrap
from csv_wrangler.splitter_col import ColSplitSpec, split_column


SAMPLE = textwrap.dedent("""\
    full_name,email,city
    Alice Johnson,alice@example.com,New York
    Bob Smith,bob@example.com,Los Angeles
    Carol White,carol@example.com,Chicago
""").strip()


def _parse_csv(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def test_row_count_preserved():
    rows = _parse_csv(SAMPLE)
    spec = ColSplitSpec(column="full_name", delimiter=" ", into=["first", "last"])
    out, result = split_column(rows, spec)
    assert len(out) == 3
    assert result.rows_processed == 3


def test_first_names_correct():
    rows = _parse_csv(SAMPLE)
    spec = ColSplitSpec(column="full_name", delimiter=" ", into=["first", "last"])
    out, _ = split_column(rows, spec)
    first_names = [r["first"] for r in out]
    assert first_names == ["Alice", "Bob", "Carol"]


def test_last_names_correct():
    rows = _parse_csv(SAMPLE)
    spec = ColSplitSpec(column="full_name", delimiter=" ", into=["first", "last"])
    out, _ = split_column(rows, spec)
    last_names = [r["last"] for r in out]
    assert last_names == ["Johnson", "Smith", "White"]


def test_other_columns_intact():
    rows = _parse_csv(SAMPLE)
    spec = ColSplitSpec(column="full_name", delimiter=" ", into=["first", "last"])
    out, _ = split_column(rows, spec)
    assert out[0]["email"] == "alice@example.com"
    assert out[2]["city"] == "Chicago"


def test_email_split_by_at():
    rows = _parse_csv(SAMPLE)
    spec = ColSplitSpec(column="email", delimiter="@", into=["local", "domain"])
    out, _ = split_column(rows, spec)
    assert out[0]["local"] == "alice"
    assert out[0]["domain"] == "example.com"
