"""CLI integration tests for the 'slice' sub-command."""
import argparse
import csv
import io
from pathlib import Path

import pytest

from csv_wrangler.cli_slice import add_slice_subcommand, _run_slice


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_slice_subcommand(sub)
    return p


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


_SOURCE = [{"id": str(i), "val": str(i)} for i in range(10)]


def test_slice_default_keeps_all(tmp_path):
    src = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    _write_csv(src, _SOURCE)
    parser = _make_parser()
    args = parser.parse_args(["slice", str(src), "-o", str(out)])
    rc = args.func(args)
    assert rc == 0
    assert len(_read_csv(out)) == 10


def test_slice_start_trims_head(tmp_path):
    src = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    _write_csv(src, _SOURCE)
    parser = _make_parser()
    args = parser.parse_args(["slice", str(src), "--start", "3", "-o", str(out)])
    rc = args.func(args)
    assert rc == 0
    rows = _read_csv(out)
    assert rows[0]["id"] == "3"
    assert len(rows) == 7


def test_slice_end_trims_tail(tmp_path):
    src = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    _write_csv(src, _SOURCE)
    parser = _make_parser()
    args = parser.parse_args(["slice", str(src), "--end", "4", "-o", str(out)])
    rc = args.func(args)
    assert rc == 0
    rows = _read_csv(out)
    assert [r["id"] for r in rows] == ["0", "1", "2", "3"]


def test_slice_window(tmp_path):
    src = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    _write_csv(src, _SOURCE)
    parser = _make_parser()
    args = parser.parse_args(
        ["slice", str(src), "--start", "2", "--end", "5", "-o", str(out)]
    )
    rc = args.func(args)
    assert rc == 0
    rows = _read_csv(out)
    assert [r["id"] for r in rows] == ["2", "3", "4"]


def test_slice_invalid_range_returns_error(tmp_path):
    src = tmp_path / "in.csv"
    _write_csv(src, _SOURCE)
    parser = _make_parser()
    args = parser.parse_args(
        ["slice", str(src), "--start", "5", "--end", "3"]
    )
    rc = args.func(args)
    assert rc == 1
