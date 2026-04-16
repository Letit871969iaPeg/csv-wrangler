"""Tests for csv_wrangler.cli_stack."""
import csv
import io
import pytest
from argparse import ArgumentParser
from csv_wrangler.cli_stack import add_stack_subcommand, _run_stack


def _make_parser():
    p = ArgumentParser()
    sub = p.add_subparsers()
    add_stack_subcommand(sub)
    return p


def _write_csv(tmp_path, name, rows):
    p = tmp_path / name
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return str(p)


def _read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def test_subcommand_registered():
    p = _make_parser()
    args = p.parse_args(["stack", "input.csv", "--id-columns", "id"])
    assert hasattr(args, "func")


def test_basic_stack(tmp_path):
    src = _write_csv(tmp_path, "in.csv", [
        {"id": "1", "jan": "10", "feb": "20"},
        {"id": "2", "jan": "30", "feb": "40"},
    ])
    out = str(tmp_path / "out.csv")
    p = _make_parser()
    args = p.parse_args(["stack", src, "--id-columns", "id", "-o", out])
    rc = _run_stack(args)
    assert rc == 0
    rows = _read_csv(out)
    assert len(rows) == 4


def test_custom_key_value_columns(tmp_path):
    src = _write_csv(tmp_path, "in.csv", [{"id": "1", "x": "5"}])
    out = str(tmp_path / "out.csv")
    p = _make_parser()
    args = p.parse_args([
        "stack", src, "--id-columns", "id",
        "--key-column", "metric", "--value-column", "amount",
        "-o", out,
    ])
    _run_stack(args)
    rows = _read_csv(out)
    assert "metric" in rows[0]
    assert "amount" in rows[0]


def test_missing_id_column_returns_error(tmp_path):
    src = _write_csv(tmp_path, "in.csv", [{"a": "1", "b": "2"}])
    out = str(tmp_path / "out.csv")
    p = _make_parser()
    args = p.parse_args(["stack", src, "--id-columns", "missing", "-o", out])
    rc = _run_stack(args)
    assert rc == 1
