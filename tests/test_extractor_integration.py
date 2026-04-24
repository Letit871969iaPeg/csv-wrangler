"""Integration tests for the extractor module using real CSV data."""
import csv
import io
import textwrap

from csv_wrangler.extractor import ExtractSpec, extract_rows


CSV_DATA = textwrap.dedent("""\
    id,email,profile_url
    1,alice@example.com,https://example.com/users/alice
    2,bob@corp.org,https://corp.org/users/bob
    3,carol@mail.net,https://mail.net/users/carol
    4,noemail,https://mail.net/users/dave
""").strip()


def _parse_csv(data: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data)))


def _run(rows, specs):
    it, result = extract_rows(iter(rows), specs)
    return list(it), result


def test_row_count_preserved():
    rows = _parse_csv(CSV_DATA)
    spec = ExtractSpec(column="email", pattern=r"@(.+)", dest="domain")
    out, _ = _run(rows, [spec])
    assert len(out) == 4


def test_domain_extraction_correct():
    rows = _parse_csv(CSV_DATA)
    spec = ExtractSpec(column="email", pattern=r"@(.+)", dest="domain")
    out, result = _run(rows, [spec])
    assert out[0]["domain"] == "example.com"
    assert out[1]["domain"] == "corp.org"
    assert out[2]["domain"] == "mail.net"
    assert result.matched_count == 3


def test_no_match_uses_fallback():
    rows = _parse_csv(CSV_DATA)
    spec = ExtractSpec(column="email", pattern=r"@(.+)", dest="domain", on_no_match="unknown")
    out, result = _run(rows, [spec])
    assert out[3]["domain"] == "unknown"
    assert result.unmatched_count == 1


def test_url_path_extraction():
    rows = _parse_csv(CSV_DATA)
    spec = ExtractSpec(column="profile_url", pattern=r"/users/([^/]+)$", dest="username")
    out, _ = _run(rows, [spec])
    assert out[0]["username"] == "alice"
    assert out[2]["username"] == "carol"


def test_multiple_specs_applied():
    rows = _parse_csv(CSV_DATA)
    specs = [
        ExtractSpec(column="email", pattern=r"@(.+)", dest="domain"),
        ExtractSpec(column="profile_url", pattern=r"/users/([^/]+)$", dest="username"),
    ]
    out, result = _run(rows, specs)
    assert out[0]["domain"] == "example.com"
    assert out[0]["username"] == "alice"
    assert result.matched_count == 7  # 3 email matches + 4 url matches


def test_original_columns_intact():
    rows = _parse_csv(CSV_DATA)
    spec = ExtractSpec(column="email", pattern=r"@(.+)", dest="domain")
    out, _ = _run(rows, [spec])
    assert out[0]["id"] == "1"
    assert out[0]["email"] == "alice@example.com"
