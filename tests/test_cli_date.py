"""Tests for csv_wrangler.cli_date."""
import argparse
import csv
import io
import os
import tempfile
import pytest

from csv_wrangler.cli_date import add_date_subcommand, _parse_specs, _run_date
from csv_wrangler.dateparser import DateParseError


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_date_subcommand(sub)
    return p


def _write_csv(path: str, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _read_csv(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_parse_spec_column_only():
    specs = _parse_specs(["dob"])
    assert specs[0].column == "dob"
    assert specs[0].in_format is None
    assert specs[0].out_format == "%Y-%m-%d"


def test_parse_spec_with_formats():
    specs = _parse_specs(["dob:%d/%m/%Y:%Y%m%d"])
    assert specs[0].in_format == "%d/%m/%Y"
    assert specs[0].out_format == "%Y%m%d"


def test_parse_spec_with_dest():
    specs = _parse_specs(["dob::%Y-%m-%d:dob_clean"])
    assert specs[0].dest == "dob_clean"


def test_subcommand_registered():
    p = _make_parser()
    args = p.parse_args(["parse-dates", "/dev/null"])
    assert hasattr(args, "func")


def test_basic_reformat():
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.csv")
        out = os.path.join(td, "out.csv")
        _write_csv(src, [{"name": "Alice", "dob": "15/03/2024"}])
        p = _make_parser()
        args = p.parse_args(["parse-dates", src, "--spec", "dob", "-o", out])
        rc = args.func(args)
        assert rc == 0
        rows = _read_csv(out)
        assert rows[0]["dob"] == "2024-03-15"


def test_dest_column_created():
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.csv")
        out = os.path.join(td, "out.csv")
        _write_csv(src, [{"dob": "2024-03-15"}])
        p = _make_parser()
        args = p.parse_args(["parse-dates", src, "--spec", "dob::%Y-%m-%d:dob2", "-o", out])
        args.func(args)
        rows = _read_csv(out)
        assert "dob2" in rows[0]
