"""Tests for csv_wrangler.cli_annotate."""

from __future__ import annotations

import argparse
import csv
import io
import os

import pytest

from csv_wrangler.cli_annotate import _parse_specs, add_annotate_subcommand, _run_annotate
from csv_wrangler.annotator import AnnotateError


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_annotate_subcommand(sub)
    return p


def _write_csv(path: str, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# _parse_specs
# ---------------------------------------------------------------------------

def test_parse_spec_valid():
    specs = _parse_specs(["upper=row['name'].upper()"])
    assert specs[0].column == "upper"


def test_parse_spec_missing_equals_raises():
    with pytest.raises(AnnotateError, match="expected"):
        _parse_specs(["nodivider"])


def test_parse_spec_bad_syntax_raises():
    with pytest.raises(AnnotateError, match="syntax error"):
        _parse_specs(["x=("])


# ---------------------------------------------------------------------------
# _run_annotate via CLI
# ---------------------------------------------------------------------------

def test_annotate_adds_column(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(str(src), [{"name": "alice"}, {"name": "bob"}])

    parser = _make_parser()
    args = parser.parse_args(
        ["annotate", str(src), "-o", str(dst), "-c", "upper=row['name'].upper()"]
    )
    rc = args.func(args)
    assert rc == 0
    rows = _read_csv(str(dst))
    assert rows[0]["upper"] == "ALICE"
    assert rows[1]["upper"] == "BOB"


def test_annotate_multiple_specs(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(str(src), [{"a": "3", "b": "4"}])

    parser = _make_parser()
    args = parser.parse_args(
        [
            "annotate", str(src), "-o", str(dst),
            "-c", "tag=\"ok\"",
            "-c", "a_copy=row['a']",
        ]
    )
    rc = args.func(args)
    assert rc == 0
    rows = _read_csv(str(dst))
    assert rows[0]["tag"] == "ok"
    assert rows[0]["a_copy"] == "3"


def test_annotate_invalid_spec_returns_error(tmp_path):
    src = tmp_path / "in.csv"
    _write_csv(str(src), [{"x": "1"}])

    parser = _make_parser()
    args = parser.parse_args(["annotate", str(src), "-c", "bad_spec"])
    rc = args.func(args)
    assert rc == 1
