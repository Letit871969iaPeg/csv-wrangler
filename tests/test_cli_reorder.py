"""Tests for csv_wrangler.cli_reorder."""
import argparse
import csv
import io
from pathlib import Path

import pytest

from csv_wrangler.cli_reorder import add_reorder_subcommand, _run_reorder


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_reorder_subcommand(sub)
    return p


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_reorder_basic(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(src, [{"a": "1", "b": "2", "c": "3"}])
    p = _make_parser()
    args = p.parse_args(["reorder", str(src), "c", "a", "b", "-o", str(dst)])
    rc = args.func(args)
    assert rc == 0
    out = _read_csv(dst)
    assert list(out[0].keys()) == ["c", "a", "b"]


def test_drop_rest_removes_unlisted(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(src, [{"a": "1", "b": "2", "c": "3"}])
    p = _make_parser()
    args = p.parse_args(["reorder", str(src), "a", "--drop-rest", "-o", str(dst)])
    rc = args.func(args)
    assert rc == 0
    out = _read_csv(dst)
    assert list(out[0].keys()) == ["a"]
    assert "b" not in out[0]


def test_missing_column_returns_error(tmp_path):
    src = tmp_path / "in.csv"
    _write_csv(src, [{"a": "1", "b": "2"}])
    p = _make_parser()
    args = p.parse_args(["reorder", str(src), "a", "z"])
    rc = args.func(args)
    assert rc == 1


def test_values_preserved_after_reorder(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(src, [{"x": "hello", "y": "world"}])
    p = _make_parser()
    args = p.parse_args(["reorder", str(src), "y", "x", "-o", str(dst)])
    args.func(args)
    out = _read_csv(dst)
    assert out[0]["x"] == "hello"
    assert out[0]["y"] == "world"
