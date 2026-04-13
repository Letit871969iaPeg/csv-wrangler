"""Integration tests for the encode CLI sub-command."""
from __future__ import annotations

import base64
import csv
import hashlib
import io
from argparse import ArgumentParser

import pytest

from csv_wrangler.cli_encode import add_encode_subcommand, _parse_specs, _run_encode
from csv_wrangler.encoder import EncodeError


def _make_parser() -> ArgumentParser:
    p = ArgumentParser()
    sub = p.add_subparsers()
    add_encode_subcommand(sub)
    return p


def _write_csv(tmp_path, rows, filename="input.csv"):
    path = tmp_path / filename
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return str(path)


def _read_csv(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# _parse_specs
# ---------------------------------------------------------------------------


def test_parse_spec_two_parts():
    specs = _parse_specs(["email:md5"])
    assert specs[0].column == "email"
    assert specs[0].scheme == "md5"
    assert specs[0].dest == "email"


def test_parse_spec_three_parts():
    specs = _parse_specs(["email:md5:email_hash"])
    assert specs[0].dest == "email_hash"


def test_parse_spec_missing_scheme_raises():
    with pytest.raises(EncodeError):
        _parse_specs(["email"])


# ---------------------------------------------------------------------------
# CLI round-trip
# ---------------------------------------------------------------------------


def test_base64_via_cli(tmp_path):
    src = _write_csv(tmp_path, [{"name": "Alice", "score": "10"}])
    out = str(tmp_path / "out.csv")
    p = _make_parser()
    args = p.parse_args(["encode", src, "-o", out, "-e", "name:base64"])
    rc = args.func(args)
    assert rc == 0
    rows = _read_csv(out)
    assert rows[0]["name"] == base64.b64encode(b"Alice").decode()


def test_md5_via_cli(tmp_path):
    src = _write_csv(tmp_path, [{"email": "user@example.com"}])
    out = str(tmp_path / "out.csv")
    p = _make_parser()
    args = p.parse_args(["encode", src, "-o", out, "-e", "email:md5:email_hash"])
    args.func(args)
    rows = _read_csv(out)
    assert rows[0]["email_hash"] == hashlib.md5(b"user@example.com").hexdigest()


def test_invalid_scheme_returns_error(tmp_path):
    src = _write_csv(tmp_path, [{"x": "1"}])
    out = str(tmp_path / "out.csv")
    p = _make_parser()
    args = p.parse_args(["encode", src, "-o", out, "-e", "x:rot13"])
    rc = args.func(args)
    assert rc == 1


def test_multiple_specs_via_cli(tmp_path):
    src = _write_csv(tmp_path, [{"a": "foo", "b": "bar"}])
    out = str(tmp_path / "out.csv")
    p = _make_parser()
    args = p.parse_args(["encode", src, "-o", out, "-e", "a:hex", "-e", "b:base64"])
    rc = args.func(args)
    assert rc == 0
    rows = _read_csv(out)
    assert rows[0]["a"] == b"foo".hex()
    assert rows[0]["b"] == base64.b64encode(b"bar").decode()
