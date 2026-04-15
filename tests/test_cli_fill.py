"""Integration tests for the fill CLI sub-command."""
from __future__ import annotations

import argparse
import csv
import io
import textwrap
from pathlib import Path

import pytest

from csv_wrangler.cli_fill import _parse_specs, add_fill_subcommand, _run_fill
from csv_wrangler.filler import FillError


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_fill_subcommand(sub)
    return p


def _write_csv(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8")))


# ---------------------------------------------------------------------------
# _parse_specs unit tests
# ---------------------------------------------------------------------------

def test_parse_spec_constant_with_value():
    specs = _parse_specs(["age:constant:0"])
    assert specs[0].column == "age"
    assert specs[0].strategy == "constant"
    assert specs[0].value == "0"


def test_parse_spec_forward_no_value():
    specs = _parse_specs(["city:forward"])
    assert specs[0].strategy == "forward"
    assert specs[0].value == ""


def test_parse_spec_too_few_parts_raises():
    with pytest.raises(FillError, match="Invalid fill spec"):
        _parse_specs(["nocolon"])


def test_parse_spec_invalid_strategy_raises():
    with pytest.raises(FillError):
        _parse_specs(["col:median"])


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

def test_fill_constant_via_cli(tmp_path: Path):
    src = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    _write_csv(src, """\
        name,age
        Alice,
        Bob,30
    """)
    parser = _make_parser()
    args = parser.parse_args(["fill", str(src), "-o", str(out), "-s", "age:constant:0"])
    rc = args.func(args)
    assert rc == 0
    rows = _read_csv(out)
    assert rows[0]["age"] == "0"
    assert rows[1]["age"] == "30"


def test_fill_forward_via_cli(tmp_path: Path):
    src = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    _write_csv(src, """\
        city,score
        NYC,10
        ,20
        ,30
    """)
    parser = _make_parser()
    args = parser.parse_args(["fill", str(src), "-o", str(out), "-s", "city:forward"])
    rc = args.func(args)
    assert rc == 0
    rows = _read_csv(out)
    assert rows[1]["city"] == "NYC"
    assert rows[2]["city"] == "NYC"


def test_missing_column_returns_error(tmp_path: Path):
    src = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    _write_csv(src, "name\nAlice\n")
    parser = _make_parser()
    args = parser.parse_args(["fill", str(src), "-o", str(out), "-s", "age:constant:0"])
    rc = args.func(args)
    assert rc == 1
