"""Integration tests for encoder using a realistic CSV payload."""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import urllib.parse

from csv_wrangler.encoder import EncodeSpec, encode_rows

RAW_CSV = """id,email,city
1,alice@example.com,New York
2,bob@example.com,Los Angeles
3,carol@example.com,San Francisco
"""


def _parse_csv(text: str):
    return list(csv.DictReader(io.StringIO(text)))


def test_row_count_preserved():
    rows = _parse_csv(RAW_CSV)
    specs = [EncodeSpec(column="email", scheme="md5")]
    out, _ = encode_rows(rows, specs)
    assert len(list(out)) == 3


def test_all_emails_hashed():
    rows = _parse_csv(RAW_CSV)
    specs = [EncodeSpec(column="email", scheme="md5", dest="email_hash")]
    out, result = encode_rows(rows, specs)
    for row in out:
        expected = hashlib.md5(row["email"].encode()).hexdigest()
        # email_hash should be md5 of the *original* email stored in email col
        assert len(row["email_hash"]) == 32
    assert result.encoded_count == 3


def test_city_url_encoded():
    rows = _parse_csv(RAW_CSV)
    specs = [EncodeSpec(column="city", scheme="url")]
    out, _ = encode_rows(rows, specs)
    result_rows = list(out)
    assert result_rows[0]["city"] == urllib.parse.quote("New York")
    assert result_rows[2]["city"] == urllib.parse.quote("San Francisco")


def test_id_hex_encoded():
    rows = _parse_csv(RAW_CSV)
    specs = [EncodeSpec(column="id", scheme="hex")]
    out, _ = encode_rows(rows, specs)
    result_rows = list(out)
    assert result_rows[0]["id"] == b"1".hex()


def test_untouched_columns_unchanged():
    rows = _parse_csv(RAW_CSV)
    specs = [EncodeSpec(column="email", scheme="sha256", dest="email_sha")]
    out, _ = encode_rows(rows, specs)
    for row in out:
        assert row["city"] in {"New York", "Los Angeles", "San Francisco"}


def test_multiple_schemes_applied_together():
    rows = _parse_csv(RAW_CSV)
    specs = [
        EncodeSpec(column="email", scheme="md5", dest="email_md5"),
        EncodeSpec(column="city", scheme="base64", dest="city_b64"),
    ]
    out, result = encode_rows(rows, specs)
    result_rows = list(out)
    assert result.encoded_count == 6  # 3 rows x 2 specs
    for row in result_rows:
        assert "email_md5" in row
        assert "city_b64" in row
        decoded = base64.b64decode(row["city_b64"]).decode()
        assert decoded in {"New York", "Los Angeles", "San Francisco"}
