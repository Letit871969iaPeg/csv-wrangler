"""Integration tests for the *cast* CLI sub-command."""
from __future__ import annotations

import csv
import io
import textwrap
from argparse import ArgumentParser
from pathlib import Path

import pytest

from csv_wrangler.cli_cast import add_cast_subcommand, _run_cast


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_parser() -> ArgumentParser:
    p = ArgumentParser()
    sub = p.add_subparsers()
    add_cast_subcommand(sub)
    return p


def _write_csv(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content))


def _read_csv(path: Path):
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_cast_int_column(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(src, "name,age\nAlice,30\nBob,25\n")

    parser = _make_parser()
    args = parser.parse_args(["cast", str(src), "-o", str(dst), "-c", "age:int"])
    rc = _run_cast(args)

    assert rc == 0
    rows = _read_csv(dst)
    # DictWriter writes str, so we compare string representation
    assert rows[0]["age"] == "30"
    assert rows[0]["name"] == "Alice"


def test_cast_invalid_spec_returns_error(tmp_path):
    src = tmp_path / "in.csv"
    _write_csv(src, "x\n1\n")

    parser = _make_parser()
    args = parser.parse_args(["cast", str(src), "-c", "bad-spec"])
    rc = _run_cast(args)
    assert rc == 1


def test_cast_strict_bad_value_returns_error(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(src, "age\nabc\n")

    parser = _make_parser()
    args = parser.parse_args(["cast", str(src), "-o", str(dst), "-c", "age:int"])
    rc = _run_cast(args)
    assert rc == 1


def test_cast_lenient_bad_value_passes_through(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(src, "age\nabc\n")

    parser = _make_parser()
    args = parser.parse_args(
        ["cast", str(src), "-o", str(dst), "-c", "age:int", "--lenient"]
    )
    rc = _run_cast(args)
    assert rc == 0
    rows = _read_csv(dst)
    assert rows[0]["age"] == "abc"


def test_cast_bool_column(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(src, "active\ntrue\nfalse\n")

    parser = _make_parser()
    args = parser.parse_args(["cast", str(src), "-o", str(dst), "-c", "active:bool"])
    rc = _run_cast(args)
    assert rc == 0
    rows = _read_csv(dst)
    assert rows[0]["active"] == "True"
    assert rows[1]["active"] == "False"
