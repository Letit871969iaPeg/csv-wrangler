"""Tests for csv_wrangler.cli_group."""
from __future__ import annotations

import csv
import io
from argparse import ArgumentParser
from pathlib import Path

import pytest

from csv_wrangler.cli_group import add_group_subcommand, _run_group


def _make_parser() -> ArgumentParser:
    p = ArgumentParser()
    sub = p.add_subparsers()
    add_group_subcommand(sub)
    return p


def _write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------------

def test_group_subcommand_registered():
    p = _make_parser()
    ns = p.parse_args(["group", "some.csv", "-k", "city"])
    assert ns.keys == ["city"]


def test_default_count_column():
    p = _make_parser()
    ns = p.parse_args(["group", "some.csv", "-k", "city"])
    assert ns.count_column == "_count"


def test_custom_count_column():
    p = _make_parser()
    ns = p.parse_args(["group", "some.csv", "-k", "city", "-c", "n"])
    assert ns.count_column == "n"


# ---------------------------------------------------------------------------
# _run_group integration
# ---------------------------------------------------------------------------

def test_group_writes_correct_groups(tmp_path):
    src = tmp_path / "input.csv"
    out = tmp_path / "output.csv"
    _write_csv(src, [
        {"city": "NYC", "name": "Alice"},
        {"city": "LA",  "name": "Bob"},
        {"city": "NYC", "name": "Carol"},
    ])
    p = _make_parser()
    ns = p.parse_args(["group", str(src), "-k", "city", "-o", str(out)])
    rc = _run_group(ns)
    assert rc == 0
    rows = _read_csv(out)
    counts = {r["city"]: int(r["_count"]) for r in rows}
    assert counts["NYC"] == 2
    assert counts["LA"] == 1


def test_group_missing_key_returns_error(tmp_path):
    src = tmp_path / "input.csv"
    _write_csv(src, [{"city": "NYC", "name": "Alice"}])
    p = _make_parser()
    ns = p.parse_args(["group", str(src), "-k", "country"])
    rc = _run_group(ns)
    assert rc == 1


def test_group_multi_key(tmp_path):
    src = tmp_path / "input.csv"
    out = tmp_path / "output.csv"
    _write_csv(src, [
        {"dept": "Eng", "level": "senior"},
        {"dept": "Eng", "level": "junior"},
        {"dept": "Eng", "level": "senior"},
        {"dept": "HR",  "level": "senior"},
    ])
    p = _make_parser()
    ns = p.parse_args(
        ["group", str(src), "-k", "dept", "-k", "level", "-o", str(out)]
    )
    rc = _run_group(ns)
    assert rc == 0
    rows = _read_csv(out)
    assert len(rows) == 3
