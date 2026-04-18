"""Tests for csv_wrangler.cli_split_col."""
import argparse
import csv
import io
import os
import tempfile
import pytest
from csv_wrangler.cli_split_col import add_split_col_subcommand, _run_split_col


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_split_col_subcommand(sub)
    return p


def _write_csv(path: str, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_subcommand_registered():
    p = _make_parser()
    args = p.parse_args(["split-col", "-", "-c", "name", "-d", " ", "-i", "first", "last"])
    assert hasattr(args, "func")


def test_basic_split(tmp_path):
    src = str(tmp_path / "in.csv")
    dst = str(tmp_path / "out.csv")
    _write_csv(src, [{"name": "John Doe", "age": "30"}, {"name": "Jane Smith", "age": "25"}])
    p = _make_parser()
    args = p.parse_args(["split-col", src, "-o", dst, "-c", "name", "-d", " ", "-i", "first", "last"])
    rc = _run_split_col(args)
    assert rc == 0
    rows = _read_csv(dst)
    assert rows[0]["first"] == "John"
    assert rows[0]["last"] == "Doe"
    assert "name" not in rows[0]


def test_keep_source(tmp_path):
    src = str(tmp_path / "in.csv")
    dst = str(tmp_path / "out.csv")
    _write_csv(src, [{"name": "John Doe"}])
    p = _make_parser()
    args = p.parse_args(["split-col", src, "-o", dst, "-c", "name", "-d", " ", "-i", "first", "last", "--keep-source"])
    rc = _run_split_col(args)
    assert rc == 0
    rows = _read_csv(dst)
    assert "name" in rows[0]


def test_invalid_spec_returns_error(tmp_path):
    src = str(tmp_path / "in.csv")
    _write_csv(src, [{"name": "John"}])
    p = _make_parser()
    args = p.parse_args(["split-col", src, "-c", "name", "-d", " ", "-i", "only"])
    rc = _run_split_col(args)
    assert rc == 1
