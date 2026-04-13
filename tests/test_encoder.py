"""Tests for csv_wrangler.encoder."""
from __future__ import annotations

import base64
import hashlib
import urllib.parse

import pytest

from csv_wrangler.encoder import EncodeError, EncodeResult, EncodeSpec, encode_rows


def _row(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# EncodeSpec
# ---------------------------------------------------------------------------


class TestEncodeSpec:
    def test_valid_scheme_accepted(self):
        spec = EncodeSpec(column="email", scheme="base64")
        assert spec.scheme == "base64"

    def test_invalid_scheme_raises(self):
        with pytest.raises(EncodeError, match="Unsupported scheme"):
            EncodeSpec(column="x", scheme="rot13")

    def test_dest_defaults_to_column(self):
        spec = EncodeSpec(column="name", scheme="hex")
        assert spec.dest == "name"

    def test_explicit_dest_preserved(self):
        spec = EncodeSpec(column="name", scheme="hex", dest="name_hex")
        assert spec.dest == "name_hex"


# ---------------------------------------------------------------------------
# encode_rows
# ---------------------------------------------------------------------------


def test_base64_encoding():
    rows = [_row(val="hello")]
    spec = EncodeSpec(column="val", scheme="base64")
    out, result = encode_rows(rows, [spec])
    row = next(out)
    assert row["val"] == base64.b64encode(b"hello").decode()
    assert result.encoded_count == 1


def test_hex_encoding():
    rows = [_row(val="hi")]
    spec = EncodeSpec(column="val", scheme="hex")
    out, _ = encode_rows(rows, [spec])
    assert next(out)["val"] == b"hi".hex()


def test_url_encoding():
    rows = [_row(val="hello world")]
    spec = EncodeSpec(column="val", scheme="url")
    out, _ = encode_rows(rows, [spec])
    assert next(out)["val"] == urllib.parse.quote("hello world")


def test_md5_encoding():
    rows = [_row(val="secret")]
    spec = EncodeSpec(column="val", scheme="md5")
    out, _ = encode_rows(rows, [spec])
    assert next(out)["val"] == hashlib.md5(b"secret").hexdigest()


def test_sha256_encoding():
    rows = [_row(val="data")]
    spec = EncodeSpec(column="val", scheme="sha256")
    out, _ = encode_rows(rows, [spec])
    assert next(out)["val"] == hashlib.sha256(b"data").hexdigest()


def test_dest_column_written():
    rows = [_row(email="user@example.com")]
    spec = EncodeSpec(column="email", scheme="md5", dest="email_hash")
    out, _ = encode_rows(rows, [spec])
    row = next(out)
    assert "email_hash" in row
    assert "email" in row  # original preserved


def test_missing_column_skipped():
    rows = [_row(name="Alice")]
    spec = EncodeSpec(column="missing", scheme="hex")
    out, result = encode_rows(rows, [spec])
    list(out)  # consume
    assert "missing" in result.skipped_columns
    assert result.encoded_count == 0


def test_empty_input_returns_empty():
    out, result = encode_rows([], [EncodeSpec(column="x", scheme="hex")])
    assert list(out) == []
    assert result.encoded_count == 0


def test_multiple_specs_multiple_counts():
    rows = [_row(a="foo", b="bar")]
    specs = [
        EncodeSpec(column="a", scheme="hex"),
        EncodeSpec(column="b", scheme="base64"),
    ]
    out, result = encode_rows(rows, specs)
    list(out)
    assert result.encoded_count == 2


def test_encode_result_str():
    r = EncodeResult(encoded_count=3, skipped_columns=["x"])
    assert "3" in str(r)
    assert "x" in str(r)
