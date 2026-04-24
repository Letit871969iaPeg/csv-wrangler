"""CLI-level tests for the zip subcommand."""
import argparse
import csv
import io
import os
import pytest

from csv_wrangler.cli_zip import add_zip_subcommand, _run_zip


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_zip_subcommand(sub)
    return p


def _write_csv(path: str, rows, fieldnames=None) -> None:
    if not rows:
        return
    fnames = fieldnames or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fnames)
        w.writeheader()
        w.writerows(rows)


def _read_csv(path: str):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_subcommand_registered():
    p = _make_parser()
    args = p.parse_args(["zip", "a.csv", "b.csv"])
    assert hasattr(args, "func")


def test_basic_zip(tmp_path):
    left = tmp_path / "left.csv"
    right = tmp_path / "right.csv"
    out = tmp_path / "out.csv"

    _write_csv(str(left), [{"name": "Alice"}, {"name": "Bob"}])
    _write_csv(str(right), [{"score": "10"}, {"score": "20"}])

    p = _make_parser()
    args = p.parse_args(["zip", str(left), str(right), "-o", str(out)])
    rc = _run_zip(args)
    assert rc == 0

    rows = _read_csv(str(out))
    assert len(rows) == 2
    assert rows[0]["left_name"] == "Alice"
    assert rows[0]["right_score"] == "10"


def test_custom_prefixes(tmp_path):
    left = tmp_path / "left.csv"
    right = tmp_path / "right.csv"
    out = tmp_path / "out.csv"

    _write_csv(str(left), [{"x": "1"}])
    _write_csv(str(right), [{"x": "2"}])

    p = _make_parser()
    args = p.parse_args([
        "zip", str(left), str(right),
        "--left-prefix", "A_",
        "--right-prefix", "B_",
        "-o", str(out),
    ])
    rc = _run_zip(args)
    assert rc == 0

    rows = _read_csv(str(out))
    assert "A_x" in rows[0]
    assert "B_x" in rows[0]


def test_strict_mismatch_returns_error(tmp_path):
    left = tmp_path / "left.csv"
    right = tmp_path / "right.csv"

    _write_csv(str(left), [{"a": "1"}, {"a": "2"}])
    _write_csv(str(right), [{"b": "x"}])

    p = _make_parser()
    args = p.parse_args(["zip", str(left), str(right), "--strict"])
    rc = _run_zip(args)
    assert rc == 1


def test_missing_file_returns_error(tmp_path):
    p = _make_parser()
    args = p.parse_args(["zip", "nonexistent_left.csv", "nonexistent_right.csv"])
    rc = _run_zip(args)
    assert rc == 1
